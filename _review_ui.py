from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app.py", default_timeout=120)
at.session_state["is_licensed"] = True
at.run()
assert not at.exception, at.exception
labels = [button.label for button in at.button]
assert "Another three" in labels, labels
assert any(box.label == "Category" for box in at.selectbox)

for radio in at.radio:
    if radio.label == "Difficulty":
        radio.set_value("Challenging (IB exam-trap)")
for box in at.multiselect:
    if box.label == "Level":
        box.set_value([1])
at.run()
assert not at.exception, at.exception
messages = [item.value for item in at.info]
print("INFO", messages)
assert any("No questions match these filters" in message for message in messages)
print("ui ok")
