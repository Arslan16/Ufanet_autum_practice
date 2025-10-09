import uuid

from hypothesis import HealthCheck
from hypothesis import strategies as st

my_hypothesis_settings = {
    "max_examples": 3,
    "derandomize": False,
    "deadline": None,
    "suppress_health_check": [HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
}


@st.composite
def card_factory(draw):
    return {
        "main_label": str(uuid.uuid4())[:10],
        "description_under_label": str(uuid.uuid4())[:10],
        "obtain_method_description": str(uuid.uuid4())[:10],
        "validity_period": str(uuid.uuid4())[:10],
        "about_partner": str(uuid.uuid4())[:10],
        "promocode": str(uuid.uuid4())[:10],
        "call_to_action_link": str(uuid.uuid4())[:10],
        "call_to_action_btn_label": str(uuid.uuid4())[:10]
    }


@st.composite
def queue_factory(draw):
    name = str(uuid.uuid4())[:5]
    suffix = str(uuid.uuid4())[:10] 
    return f"{name}_{suffix}"


@st.composite
def company_factory(draw):
    name = str(uuid.uuid4())[:5]
    suffix = str(uuid.uuid4())[:10]
    short_description = str(uuid.uuid4())[:15] 
    return {"name": f"{name}_{suffix}", "short_description": short_description}


@st.composite
def category_factory(draw):
    name = str(uuid.uuid4())[:5]
    suffix = str(uuid.uuid4())[:10] 
    return {"name": f"{name}_{suffix}"}
