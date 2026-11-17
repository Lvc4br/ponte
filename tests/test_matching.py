from app.core.models import BridgeRecord,NumericRange,SearchCriteria
from app.core.matching import filter_records

def test_overlap_range():
 rows=[BridgeRecord({'largura_m':'12,0','vao_m':'41,25 - 41,80','compr_obra_m':80},1),BridgeRecord({'largura_m':'8,0','vao_m':20,'compr_obra_m':30},2)]
 result=filter_records(rows,SearchCriteria(width=NumericRange(10,14),span=NumericRange(41,42)))
 assert len(result)==1 and result[0].source_row==1

def test_missing_value_kept():
 row=BridgeRecord({'largura_m':None},1)
 assert filter_records([row],SearchCriteria(width=NumericRange(5,10)))==[row]
