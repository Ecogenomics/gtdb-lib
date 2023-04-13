import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from gtdblib.db import GenericEngine

"""
from gtdblib.db.common import DB_COMMON, LpsnHtml

from sqlalchemy import select
def main():
    with DB_COMMON as db:

        stmt = select(LpsnHtml).where(LpsnHtml.id == 1)
        res = db.execute(stmt).fetchall()

        print(res)

if __name__ == '__main__':
    main()
"""

DB_COMMON = GenericEngine('common')


class Common(DeclarativeBase):
    type_annotation_map = {
        datetime.datetime: TIMESTAMP(timezone=True),
    }


class LpsnHtml(Common):
    __tablename__ = 'lpsn_html'

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(nullable=False)
    created: Mapped[datetime.datetime] = mapped_column(nullable=False)
    updated: Mapped[datetime.datetime] = mapped_column(nullable=False)
    html: Mapped[str] = mapped_column(nullable=True)
    to_process: Mapped[bool] = mapped_column(nullable=False, default=True)

    # Output columns
    name: Mapped[str] = mapped_column(nullable=True)
    category: Mapped[str] = mapped_column(nullable=True)
    proposed_as: Mapped[str] = mapped_column(nullable=True)
    etymology: Mapped[str] = mapped_column(nullable=True)
    original_publication: Mapped[str] = mapped_column(nullable=True)
    original_publication_doi: Mapped[str] = mapped_column(nullable=True)
    nomenclatural_status: Mapped[str] = mapped_column(nullable=True)
    n_child_correct: Mapped[int] = mapped_column(nullable=True)
    n_child_synonym: Mapped[int] = mapped_column(nullable=True)
    n_child_total: Mapped[int] = mapped_column(nullable=True)
    assigned_by: Mapped[str] = mapped_column(nullable=True)
    assigned_by_doi: Mapped[str] = mapped_column(nullable=True)
    record_number: Mapped[int] = mapped_column(nullable=True)
    gender: Mapped[str] = mapped_column(nullable=True)
    valid_publication: Mapped[str] = mapped_column(nullable=True)
    valid_publication_doi: Mapped[str] = mapped_column(nullable=True)
    ijsem_list: Mapped[str] = mapped_column(nullable=True)
    ijsem_list_doi: Mapped[str] = mapped_column(nullable=True)
    taxonomic_status: Mapped[str] = mapped_column(nullable=True)
    parent_taxon: Mapped[int] = mapped_column(ForeignKey("lpsn_html.id"), nullable=True)
    type_class: Mapped[int] = mapped_column(ForeignKey("lpsn_html.id"), nullable=True)
    type_order: Mapped[int] = mapped_column(ForeignKey("lpsn_html.id"), nullable=True)
    type_genus: Mapped[int] = mapped_column(ForeignKey("lpsn_html.id"), nullable=True)
    type_subgenus: Mapped[int] = mapped_column(ForeignKey("lpsn_html.id"), nullable=True)
    type_species: Mapped[int] = mapped_column(ForeignKey("lpsn_html.id"), nullable=True)
    effective_publication: Mapped[str] = mapped_column(nullable=True)
    effective_publication_doi: Mapped[str] = mapped_column(nullable=True)
    emendations: Mapped[str] = mapped_column(nullable=True)
    tygs: Mapped[str] = mapped_column(nullable=True)
    type_strain: Mapped[str] = mapped_column(nullable=True)
    ssu_ggdc: Mapped[str] = mapped_column(nullable=True)
    ssu_fasta: Mapped[str] = mapped_column(nullable=True)
    ssu_ebi: Mapped[str] = mapped_column(nullable=True)
    ssu_ncbi: Mapped[str] = mapped_column(nullable=True)
    ssu: Mapped[str] = mapped_column(nullable=True)
    strain_info: Mapped[str] = mapped_column(nullable=True)
    risk_group: Mapped[int] = mapped_column(nullable=True)
    basonym: Mapped[int] = mapped_column(ForeignKey("lpsn_html.id"), nullable=True)

    def __repr__(self) -> str:
        return f'LpsnHtml(id={self.id!r}, url={self.url!r})'


class LpsnHtmlNotes(Common):
    __tablename__ = 'lpsn_html_notes'

    id: Mapped[int] = mapped_column(primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("lpsn_html.id"), nullable=False)
    doi: Mapped[str] = mapped_column(nullable=True)
    note: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f'LpsnHtmlNotes(id={self.id!r}, page_id={self.page_id!r})'


class LpsnHtmlChildTaxa(Common):
    __tablename__ = 'lpsn_html_child_taxa'

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_page_id: Mapped[int] = mapped_column(ForeignKey("lpsn_html.id"), nullable=False)
    child_page_id: Mapped[int] = mapped_column(ForeignKey("lpsn_html.id"), nullable=False)
    nomenclatural_status: Mapped[str] = mapped_column(nullable=True)
    taxonomic_status: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f'LpsnHtmlChildTaxa(id={self.id!r}, parent_page_id={self.parent_page_id!r}, child_page_id={self.child_page_id!r})'


class LpsnHtmlSynonyms(Common):
    __tablename__ = 'lpsn_html_synonyms'

    id: Mapped[int] = mapped_column(primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("lpsn_html.id"), nullable=False)
    synonym_id: Mapped[int] = mapped_column(ForeignKey("lpsn_html.id"), nullable=False)
    kind: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f'LpsnHtmlSynonyms(id={self.id!r}, page_id={self.page_id!r}, synonym_id={self.synonym_id!r})'


class SeqCodeHtml(Common):
    __tablename__ = 'seqcode_html'

    id: Mapped[int] = mapped_column(primary_key=True)
    updated: Mapped[datetime.datetime] = mapped_column(nullable=False, default=datetime.datetime.utcnow)
    to_process: Mapped[bool] = mapped_column(nullable=False, default=True)
    etag: Mapped[str] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column(nullable=True)
    rank: Mapped[str] = mapped_column(nullable=True)
    status_name: Mapped[str] = mapped_column(nullable=True)
    syllabification: Mapped[str] = mapped_column(nullable=True)
    priority_date: Mapped[datetime.datetime] = mapped_column(nullable=True)
    formal_styling_raw: Mapped[str] = mapped_column(nullable=True)
    formal_styling_html: Mapped[str] = mapped_column(nullable=True)
    etymology: Mapped[str] = mapped_column(nullable=True)
    type_strain: Mapped[str] = mapped_column(nullable=True)
    sc_created_at: Mapped[datetime.datetime] = mapped_column(nullable=True)
    sc_updated_at: Mapped[datetime.datetime] = mapped_column(nullable=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("seqcode_html.id"), nullable=True)
    phylum_id: Mapped[int] = mapped_column(ForeignKey("seqcode_html.id"), nullable=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("seqcode_html.id"), nullable=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("seqcode_html.id"), nullable=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("seqcode_html.id"), nullable=True)
    genus_id: Mapped[int] = mapped_column(ForeignKey("seqcode_html.id"), nullable=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("seqcode_html.id"), nullable=True)
    corrigendum_by_id: Mapped[int] = mapped_column(nullable=True)
    corrigendum_by_citation: Mapped[str] = mapped_column(nullable=True)
    corrigendum_from: Mapped[str] = mapped_column(nullable=True)
    content: Mapped[str] = mapped_column(nullable=False)
    description_raw: Mapped[str] = mapped_column(nullable=True)
    description_html: Mapped[str] = mapped_column(nullable=True)
    proposed_by_id: Mapped[int] = mapped_column(nullable=True)
    proposed_by_citation: Mapped[str] = mapped_column(nullable=True)
    notes_raw: Mapped[str] = mapped_column(nullable=True)
    notes_html: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f'SeqCodeHtml(id={self.id!r}, name={self.name!r})'


class SeqCodeHtmlChildren(Common):
    __tablename__ = 'seqcode_html_children'

    parent_id: Mapped[int] = mapped_column(ForeignKey("seqcode_html.id"), nullable=False, primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("seqcode_html.id"), nullable=False, primary_key=True)

    def __repr__(self) -> str:
        return f'SeqCodeHtmlChildren(parent_id={self.parent_id!r}, child_id={self.child_id!r})'


class SeqCodeHtmlQcWarnings(Common):
    __tablename__ = 'seqcode_html_qc_warnings'

    id: Mapped[int] = mapped_column(primary_key=True)
    sc_id: Mapped[int] = mapped_column(ForeignKey("seqcode_html.id"), nullable=False)
    can_approve: Mapped[bool] = mapped_column(nullable=True)
    text: Mapped[str] = mapped_column(nullable=False)
    rules: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f'SeqCodeHtmlQcWarnings(parent_id={self.id!r}, sc_id={self.sc_id!r})'
