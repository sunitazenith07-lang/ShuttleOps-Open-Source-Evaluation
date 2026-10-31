"""Pure presentation helper for immutable-in-practice dispatch snapshots."""
from copy import deepcopy
from explainer import explain_dispatch


def capture_decision(order, partners, travel, now=0):
    """Capture exactly the state used for a decision, without updating partners."""
    context = deepcopy({'order': order, 'partners': partners, 'travel': travel, 'now': now})
    report = explain_dispatch(context['order'], context['partners'], context['travel'], context['now'])
    return {'context': context, 'report': deepcopy(report)}
