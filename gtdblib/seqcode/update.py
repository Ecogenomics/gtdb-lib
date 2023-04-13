import json
import multiprocessing as mp
from datetime import datetime, timezone

import requests
import sqlalchemy as sa
from tqdm import tqdm

from gtdblib import log
from gtdblib.db.common import SeqCodeHtml, DB_COMMON, SeqCodeHtmlQcWarnings, SeqCodeHtmlChildren
from gtdblib.util.iterable import iter_batches

EXPECTED_KEYS = {
    'id', 'name', 'rank', 'status_name', 'syllabification', 'priority_date',
    'formal_styling', 'etymology', 'type', 'corrigendum_by', 'corrigendum_from',
    'classification', 'children', 'created_at', 'updated_at', 'url', 'qc_warnings',
    'description', 'proposed_by', 'notes'
}


def _seqcode_update_worker(content: str):
    # Convert the response to JSON
    r_json = json.loads(content)
    page_id = r_json['id']

    # Sanity check
    extra_keys = set(r_json.keys()) - EXPECTED_KEYS
    if len(extra_keys) > 0:
        raise ValueError(f'Unexpected keys: {extra_keys}')

    # Create the child rows
    children = list()
    if len(r_json.get('children', list())) > 0:
        children = [SeqCodeHtmlChildren(parent_id=page_id, child_id=x['id']) for x in r_json['children']]

    # TODO
    if r_json.get('priority_date') is not None:
        raise Exception('TODO')

    # Parse the ranks
    d_rank_to_id = dict()
    for rank in r_json.get('classification', list()):
        d_rank_to_id[rank['rank']] = rank['id']

    def sc_dt_to_obj(dt):
        if dt is None:
            return None
        return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)

    # Create the update query
    d_update = {
        'name': r_json.get('name'),
        'to_process': False,
        'rank': r_json.get('rank'),
        'status_name': r_json.get('status_name'),
        'syllabification': r_json.get('syllabification'),
        'priority_date': r_json.get('priority_date'),
        'formal_styling_raw': r_json.get('formal_styling', dict()).get('raw'),
        'formal_styling_html': r_json.get('formal_styling', dict()).get('html'),
        'etymology': r_json.get('etymology'),
        'type_strain': r_json.get('type'),
        'sc_created_at': sc_dt_to_obj(r_json.get('created_at')),
        'sc_updated_at': sc_dt_to_obj(r_json.get('updated_at')),
        'corrigendum_by_id': r_json.get('corrigendum_by', dict()).get('id'),
        'corrigendum_by_citation': r_json.get('corrigendum_by', dict()).get('citation'),
        'corrigendum_from': r_json.get('corrigendum_from'),
        'domain_id': d_rank_to_id.get('domain'),
        'phylum_id': d_rank_to_id.get('phylum'),
        'class_id': d_rank_to_id.get('class'),
        'order_id': d_rank_to_id.get('order'),
        'family_id': d_rank_to_id.get('family'),
        'genus_id': d_rank_to_id.get('genus'),
        'species_id': d_rank_to_id.get('species'),
        'description_raw': r_json.get('description', dict()).get('raw'),
        'description_html': r_json.get('description', dict()).get('html'),
        'proposed_by_id': r_json.get('proposed_by', dict()).get('id'),
        'proposed_by_citation': r_json.get('proposed_by', dict()).get('citation'),
        'notes_raw': r_json.get('notes', dict()).get('raw'),
        'notes_html': r_json.get('notes', dict()).get('html'),
    }

    # Construct the QC warnings
    qc_warnings = list()
    for warning in r_json.get('qc_warnings', list()):
        qc_warnings.append(SeqCodeHtmlQcWarnings(
            sc_id=page_id,
            can_approve=warning.get('can_approve'),
            text=warning.get('message'),
            rules=';'.join(warning['rules']) if warning.get('rules') else None,
        ))

    return page_id, d_update, qc_warnings, children


def _seqcode_get_json_worker(page_id: int):
    r = requests.get(f'https://disc-genomics.uibk.ac.at/seqcode/names/{page_id}.json')
    if not r.ok or r.url == 'https://disc-genomics.uibk.ac.at/seqcode/':
        return page_id, None
    row = SeqCodeHtml(
        id=page_id,
        etag=r.headers.get('etag'),
        content=r.text,
    )
    return page_id, row


def _get_existing_rows():
    with DB_COMMON as db:
        stmt = sa.select(SeqCodeHtml.id)
        rows = db.execute(stmt).fetchall()
        return {x.id for x in rows}


def seqcode_update(from_id: int, to_id: int, batch_size: int, cpus: int):
    """This method updates the SeqCode database with the latest data.

    :param batch_size: The number of batches between SQL update operations.
    :param cpus: The number of CPUs to use.
    """

    existing_ids = _get_existing_rows()
    log.info(f'Found {len(existing_ids):,} existing IDs that will not be processed.')

    queue = list(range(from_id, to_id))
    queue = sorted(set(queue) - existing_ids)
    log.info(f'Processing {len(queue):,} IDs within range.')

    with DB_COMMON as db:

        # Collect the page JSON content
        log.info(f'Collecting JSON content for {len(queue):,} IDs.')
        for batch in iter_batches(queue, batch_size):
            with mp.Pool(cpus) as pool:
                results = list(tqdm(pool.imap_unordered(_seqcode_get_json_worker, batch), total=len(batch)))

            rows_to_add = list()
            for page_id, row in results:
                if row is None:
                    print(f'Failed: {page_id}')
                    continue
                rows_to_add.append(row)

            # Update the database
            db.add_all(rows_to_add)
            db.commit()

        # Select all rows that exist in the database
        log.info(f'Loading JSON content from database to update.')
        stmt = sa.select(SeqCodeHtml.id, SeqCodeHtml.content) \
            .where(SeqCodeHtml.to_process == True) \
            .order_by(SeqCodeHtml.id)
        rows = db.execute(stmt).fetchall()
        queue = [x.content for x in rows]

        log.info(f'Generating DML statements.')
        with mp.Pool(cpus) as pool:
            results = list(tqdm(pool.imap_unordered(_seqcode_update_worker, queue), total=len(queue)))

        # Perform the updates/inserts
        log.info('Running inserts/updates')
        for page_id, d_update, qc_warnings, children in tqdm(results):

            # Update the main row
            stmt = sa.update(SeqCodeHtml).where(SeqCodeHtml.id == page_id).values(**d_update)
            db.execute(stmt)

            # Insert the QC warnings
            if len(qc_warnings) > 0:
                db.add_all(qc_warnings)

            # Insert the children
            if len(children) > 0:
                db.add_all(children)

            # Commit the changes
            db.commit()

    log.info('Done.')
    return
