from hypothesis import strategies as st, HealthCheck
from string import ascii_letters, digits


my_hypothesis_settings = dict(
    max_examples=3, 
    derandomize=False,
    deadline=None, 
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)

SAFE_CHARS = ascii_letters + digits

safe_text = lambda min_size, max_size: st.text(alphabet=SAFE_CHARS, min_size=min_size, max_size=max_size)

card_factory = st.fixed_dictionaries({
    "id": st.integers(min_value=100, max_value=10000),
    "main_label": safe_text(3, 20),
    "description_under_label": safe_text(3, 50),
    "obtain_method_description": safe_text(3, 50),
})

queue_factory = safe_text(5, 15)


@st.composite
def company_factory(draw):
    name = draw(safe_text(5, 10))
    suffix = draw(st.integers(1, 10000))
    short_description = draw(safe_text(10, 50))
    return {"name": f"{name}_{suffix}", "short_description": short_description}


@st.composite
def category_factory(draw):
    name = draw(safe_text(5, 10))
    suffix = draw(st.integers(1, 10000))
    return {"name": f"{name}_{suffix}"}


