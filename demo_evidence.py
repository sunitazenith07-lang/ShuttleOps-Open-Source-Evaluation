"""Read-only evidence and isolated scenario demonstrations; no engine modifications."""
from copy import deepcopy
import json
from pathlib import Path
from models import new_order, new_partner
from service import assign_order, process_cancellation

NAMES = ('Lowest ETA', 'No eligible partner', 'Equal ETA tie', 'Full capacity', 'Missing travel data', 'Inactive partner', 'Duplicate cancellation')

def scenarios():
    return NAMES


def run_scenario(name):
    if name not in NAMES:
        raise ValueError('Unknown demonstration scenario')
    order = new_order('DEMO-1', 'R-1', 'ZONE-C', 10)
    a = new_partner('P-01', 'ZONE-A', 2)
    b = new_partner('P-02', 'ZONE-B', 2)
    legs = {('ZONE-A','R-1'): 4, ('ZONE-B','R-1'): 7, ('R-1','ZONE-C'): 8}
    partners = [a,b]
    if name == 'Lowest ETA':
        expected = {'partner_id':'P-01','eta_minutes':22}
    elif name == 'No eligible partner':
        partners=[]
        expected = {'partner_id':None,'eta_minutes':None}
    elif name == 'Equal ETA tie':
        legs[('ZONE-B','R-1')]=4
        partners=[b,a]  # Reverse input order, tie must still choose P-01.
        expected={'partner_id':'P-01','eta_minutes':22}
    elif name == 'Full capacity':
        a['active_order_ids']=['SEED-1','SEED-2']
        expected={'partner_id':'P-02','eta_minutes':25}
    elif name == 'Missing travel data':
        legs.pop(('ZONE-A','R-1'))
        expected={'partner_id':'P-02','eta_minutes':25}
    elif name == 'Inactive partner':
        a['active']=False
        expected={'partner_id':'P-02','eta_minutes':25}
    else:
        a['active_order_ids']=['DEMO-1']
        a['minutes_by_order']={'DEMO-1':12}
        a['workload_minutes']=12
        initial=deepcopy(a)
        once=process_cancellation(a,'DEMO-1','EVENT-1')
        twice=process_cancellation(once,'DEMO-1','EVENT-1')
        expected={'first_active_orders':0,'first_workload':0,'second_equals_first':True,'original_unchanged':True}
        actual={'first_active_orders':len(once['active_order_ids']), 'first_workload':once['workload_minutes'], 'second_equals_first':twice==once,'original_unchanged':a==initial}
        return {'scenario':name,'expected':expected,'actual':actual,'passed':actual==expected}
    result=assign_order(order,deepcopy(partners),deepcopy(legs),0)
    actual={k:result.get(k) for k in ('partner_id','eta_minutes')}
    return {'scenario':name,'expected':expected,'actual':actual,'passed':actual==expected}


def decision_steps(snapshot):
    """Read only recorded inputs and output; never call assignment again."""
    context=snapshot['context']; report=snapshot['report']; order=context['order']; result=report['decision']
    candidates=report['candidates']; eligible=[c for c in candidates if c['eligible']]
    details=[]
    fields=('order_id','restaurant_id','destination_zone','prep_minutes')
    details.append({'title':'Input validation','description':'Recorded order fields and simulation clock; an invalid order cannot be assigned.',
                    'rows':[{'Field':k,'Value':order.get(k)} for k in fields]+[{'Field':'now','Value':context['now']}]})
    details.append({'title':'Eligibility','description':'Partner eligibility and rejection reasons as recorded before capacity was changed.',
                    'rows':[{'Partner':c['partner_id'],'Eligible':c['eligible'],'Status':c['status'],'Why':c['reason']} for c in candidates]})
    eta_rows=[]
    for c in eligible:
        p=next((p for p in context['partners'] if p['partner_id']==c['partner_id']),None)
        if not p: continue
        leg1=context['travel'].get((p['zone'],order['restaurant_id']))
        leg2=context['travel'].get((order['restaurant_id'],order['destination_zone']))
        eta_rows.append({'Partner':c['partner_id'],'Now':context['now'],'To restaurant':leg1,'Workload':p['workload_minutes'],'Pickup':c['pickup_minutes'],'Preparation':order['prep_minutes'],'To customer':leg2,'ETA':c['eta_minutes']})
    details.append({'title':'ETA calculation','description':'Pickup = now + partner travel + workload. ETA = pickup + preparation + customer travel. Unknown values are not zero.', 'rows':eta_rows})
    ranked=sorted(eligible,key=lambda c:(c['eta_minutes'],c['partner_id']))
    details.append({'title':'Ranking and tie-break','description':'Sort by ascending ETA, then lexicographic partner ID.',
                    'rows':[{'Rank':i,'Partner':c['partner_id'],'ETA':c['eta_minutes']} for i,c in enumerate(ranked,1)]})
    details.append({'title':'Final assignment','description':('Selected '+str(result['partner_id'])+' at ETA '+str(result['eta_minutes']) if result.get('partner_id') else 'Unassigned: '+str(result.get('reason'))),
                    'rows':[{'Field':k,'Value':v} for k,v in result.items()]})
    return details


def verify_test_report(path):
    try:
        info=json.loads(Path(path).read_text(encoding='utf-8'))
        valid=all(k in info for k in ('passed','failed','python','timestamp_utc','command')) and type(info['passed']) is int and type(info['failed']) is int and info['passed']>=0 and info['failed']>=0
        return {'ok':bool(valid),'report':info if valid else None,'message':'Saved test evidence is incomplete.' if not valid else ''}
    except (OSError,ValueError,TypeError) as exc:
        return {'ok':False,'report':None,'message':'No valid saved test report. Run pytest to obtain current results.'}
