import xml.etree.ElementTree as ET
import json
import re


# gets the answer from the xml given the variable name
def get_answer(et_var, variables_root):
    et_ans = variables_root.find("./Answer[@name='" + et_var + "']")

    if et_ans is not None:
        if et_ans[0].text is not None:
            return et_ans[0].text
        if et_ans[0][0].text is not None:
            return et_ans[0][0].text
    return None


# scrubs text for output into txt, removes anchor tags and replaces in text variables
def scrub(text, variables_root):
    # removes anchor tags
    text = re.sub('<[^<]*?/?>', '', text)
    # finds in text variables in for %%[variable name]%%
    in_text_variables = re.findall('%%\\[(.[^%]*)]%%', text)

    # if there are such in text variables replaced them with corresponding variables from the xml
    if len(in_text_variables):
        for in_text_variable in in_text_variables:
            in_text_answer = get_answer(in_text_variable, variables_root)

            if in_text_answer is not None:
                text = text.replace("%%[" + in_text_variable + "]%%", in_text_answer)

    return text


ANSWER_XML_FILE = ""
A2J_JSON_FILE = ""

# getting xml answer file
tree = ET.parse(ANSWER_XML_FILE)
root = tree.getroot()

# find all answered questions from xml
all_answered = []
for answer in root:
    all_answered.append(answer.attrib["name"])

# open output file to write
out = open("output.txt", "w+")

# open a2j json file
f = open(A2J_JSON_FILE, encoding="utf8")
a2j = json.load(f, )
pages = a2j["pages"]

# iterate through every page of a2j to look for pages with fields
for page in pages.values():
    fields = page["fields"]

    # check if those questions are answered
    answered = False
    if fields:
        for field in fields:
            if field["name"] in all_answered:
                answered = True

    # logic for when page is answered
    if answered:
        # output question text
        out.write("Question: \n")
        out.write(scrub(page["text"] + "\n", root))

        if len(page["learn"]):
            out.write("Learn more: \n")
            out.write(scrub(page["learn"] + "\n", root))
            out.write(scrub(page["help"] + "\n", root))
        # different answer types have different behaviour, this finds what type it is
        field_type = "text"
        for field in fields:
            match field["type"]:
                case "text":
                    pass

                case "radio":
                    field_type = "radio"

                case "checkbox":
                    field_type = "check"

        # Text answer type
        if field_type == "text":
            for field in fields:
                variable_name = field["name"]

                answer = get_answer(variable_name, root)
                if answer is not None:
                    # if answered output field label if exists, and output answer
                    if field["label"]:
                        out.write(scrub(field["label"] + "\n", root))
                    out.write(answer + "\n")

        # Radio button answer type
        if field_type == "radio":
            # gets variable for radio button
            variable_name = fields[0]["name"]
            for field in fields:
                if variable_name != field["name"]:
                    print("WARNING RADIO BUTTON MULTIPLE VARIABLES FOR VARIABLE ON PAGE: ", page["name"])

            # not checking if answer is none because radio buttons have to be pressed
            answer_var = get_answer(variable_name, root)
            answer = answer_var
            # need to get label for radio boxes as that is the actual answer

            for field in fields:
                if field["value"] == answer_var:
                    answer = scrub(field["label"], root)
            out.write(answer + "\n")

        if field_type == "check":

            # gets variable for each check box, outputs label if checked
            for field in fields:
                variable_name = field["name"]
                answer_tf = get_answer(variable_name, root)

                # output label if true
                if answer_tf is not None:
                    if answer_tf == "true":
                        answer = scrub(field["label"], root)
                        out.write(answer + "\n")

        # new line at end of information regarding this page
        out.write("\n")

out.close()
