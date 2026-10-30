from fixtures import sample_inputs
from service import assign_order


if __name__ == "__main__":
    # Direct run par sample input assign karke result print karo.
    order, partners, travel = sample_inputs()
    print(assign_order(order, partners, travel))
