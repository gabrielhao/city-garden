from langgraph.graph import StateGraph, START, END
from city_garden.garden_state import GardenState
from city_garden.city_garden_nodes import analyze_garden_conditions, generate_final_output, check_compliance, create_garden_image

def build_garden_graph():
    garden_graph = StateGraph(GardenState)
    
    garden_graph.add_node("check_compliance", check_compliance)

    garden_graph.add_node("analyze_garden_conditions", analyze_garden_conditions)

    # Add a node to generate final output
    garden_graph.add_node("generate_final_output", generate_final_output)
    garden_graph.add_node("create_garden_image", create_garden_image)
    # Define the parallel flow
    garden_graph.add_edge(START, "check_compliance")
    
    # Define the conditional flow, if check_compliance passes, analyze_garden_conditions is executed, otherwise END is executed
    garden_graph.add_conditional_edges(
        "check_compliance",
        lambda state: "analyze_garden_conditions" if state["compliance_check"] == "Pass" else END
    )

    # Connect join node to final output
    garden_graph.add_edge("analyze_garden_conditions", "generate_final_output")
    garden_graph.add_edge("generate_final_output", "create_garden_image")
    garden_graph.add_edge("create_garden_image", END)

    return garden_graph.compile()