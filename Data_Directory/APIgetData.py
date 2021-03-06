import requests as r
import json


def getData(webPage, token):
    """
    This function is responsible to get the all the data from the reports in order to be used to make the PDF
    :param webPage: The URL of the web page
    :param token: The token that will be sent as a header.
            Usually indicates that permission has been given to the given party or
            individual who is using the data.
    :return: A dictionary containing all the data
    """

    response = r.get(webPage + "api/reports", headers={"Authorization": "Token " + token,
                                                       "Content-Type": "application/json"})
    data = json.loads(response.text)

    if data['count'] > 0:
        results = data['results']  # results = list
        assessment_type_dict = dict()
        org_unit_code = list()

        # ========================================================== #
        # ========================================================== #
        # Makes the 'assessment_type' as the key. Creates a list as the VALUE
        # 0th position holds the 'assessment name'
        # 1st position holds the 'org_unit_code'
        # 2nd position holds 'unit-questions' data as a Dictionary.
        # 3rd position holds
        for key in results:
            if not assessment_type_dict.__contains__(key['assessment_type']):
                assessment_type_dict.setdefault(key['assessment_type'], dict())

            if not org_unit_code.__contains__(key['org_unit_code']):
                org_unit_code.append(key['org_unit_code'])

            val = assessment_type_dict.get(key['assessment_type'])
            if not val.get(key['org_unit_name']) is None:
                ans = val.get(key['org_unit_name'])
                code = ans.pop(len(ans) - 1)
                if code == key['org_unit_code']:
                    val[key['org_unit_name']].append(key['assessment_name'])
                val[key['org_unit_name']].append(code)

            else:
                val[key['org_unit_name']] = list()
                assessment_type_dict[key['assessment_type']][key['org_unit_name']].append(key['assessment_name'])
                assessment_type_dict[key['assessment_type']][key['org_unit_name']].append(key['org_unit_code'])

            links = key['links']
            unit_questions = links["unit-questions"]

            # Function Call
            u_questions_data = unit_questions_data(webPage, token, unit_questions)
            assessment_type_dict[key['assessment_type']][key['org_unit_name']].append(u_questions_data)

            # Function Call
            host_data = get_graph_data(webPage, token, links['self'])
            assessment_type_dict[key['assessment_type']][key['org_unit_name']].append(host_data)

        # print('response status: ' + str(response.status_code))
        return assessment_type_dict

    else:
        return "There is NO DATA present"


def unit_questions_data(webPage, token, unit_questions):
    """
    This function is responsible of getting all the Unit-Question data for the respective 'assessment_name'
    and returns a dictionary with all the data.
    :param webPage: The URL of the web page
    :param token: The token that will be sent as a header.
            Usually indicates that permission has been given to the given party or
            individual who is using the data.
    :param unit_questions: The link to the API from where the data will be taken.
    :return: A dictionary containing all the data from the specified report.
    """

    response = r.get(webPage + unit_questions, headers={"Authorization": "Token " + token,
                                                        "Content-Type": "application/json"})
    data = json.loads(response.text)
    category_id = dict()

    # Gets all the 'id' from the category and keeps it as KEYS
    # The  VALUE is a list of 'name' and 'average'
    # I have created extra 3 lists that would later be used to store the
    # 'id', 'text' and 'answer'
    for categories in data['categories']:
        category_id[categories['id']] = list()
        category_id[categories['id']].append(categories['name'])
        category_id[categories['id']].append(categories['average'])
        category_id[categories['id']].append(list())
        category_id[categories['id']].append(list())
        category_id[categories['id']].append(list())
        category_id[categories['id']].append(list())

    # Get all the questions and answers from the report.
    # VALUE is a combination of separate lists 'id', 'text' and 'answer'. This is done
    # when the 'category' from 'question' matches the key from the category_id variable.
    for questions in data['questions']:
        question = questions['question']
        answers = questions['answer']
        if question['category'] in category_id:
            category_id[question['category']][2].append(question['id'])
            category_id[question['category']][3].append(question['text'])
            category_id[question['category']][4].append(question['parent'])
            category_id[question['category']][5].append(answers)

    return category_id


def get_graph_data(webPage, token, survey_id):
    """
    Function to call the survey_id specific based API for the summary, classifications, classification and
    unit_questions. Created a list that returns all of this data back to the calling line of code.
    The list is a specific order:
            content[0] = data['classifications']
            content[1] = data['summary']
            content[2] = data['classification']
            content[3] = data['unit_questions']
    :param webPage: The URL of the web page where the data exists
    :param token: The token that will be sent as a header.
            Usually indicates that permission has been given to the given party or
            individual who is using the data.
    :param survey_id: Survey based specific ID. A basic and necessary requirement
            in order to get access of the API.
    :return: A list containing all the necessary data from the API.
    """

    response = r.get(webPage + survey_id, headers={"Authorization": "Token " + token,
                                                   "Content-Type": "application/json"})
    data = json.loads(response.text)
    content = list()
    content.append(data['classifications'])
    content.append(data['summary'])
    content.append(data['classification'])
    content.append(data['unit_questions'])

    return content


def commonReport_data(assessment_name, common_dictionary, token, webPage):
    """
    Function that creates a dictionary and passes it to the parent function to create the Common Report Heat Map
    :param webPage: The URL of the web page
    :param token: The token that will be sent as a header.
            Usually indicates that permission has been given to the given party or
            individual who is using the data.
    :param assessment_name: The required Heat Map of the specified Assessment Name
    :param common_dictionary: Dictionary:
                                    :key: assessment_name
                                    :value: Nested list
                                                Each cell of the outer list symbolised a list
                                                of [assessment_type, org_unit_name]
    :return: Dictionary:
                :key: org_unit_name
                :value: Nested List
                            [0]: Category Based Questions
                            [1]: Category Based Averages
    """
    param_1 = common_dictionary[assessment_name]
    main_dict = dict()
    for each in param_1:
        survey_id = getSurvey_ID(each[0], assessment_name, each[1], token)
        heatMap_data = heat_map_data(webPage, survey_id, token)
        z_names = list()
        for i in heatMap_data[0]:
            z_names.append(i[0])
        z_avg = heatMap_data[1]
        main_dict[each[1]] = [z_names, z_avg]

    return main_dict


def common_heat_map_data(webAPI_data):
    """
    Function that would get the common report data from the Report API.
    The reason for this function is to help in the formation of the common_report_HeatMap
    :param webAPI_data: Dictionary containing all the Data from the Report API
    :return: Dictionary:
                :key: assessment_name
                :value: Nested list
                     Each cell of the outer list symbolised a list of [assessment_type, org_unit_name]
    """

    common_dictionary = dict()
    for assessment_type in webAPI_data:
        sec_dict = webAPI_data[assessment_type]
        for org_unit_name in sec_dict:
            val = sec_dict[org_unit_name][0]
            small_lst = list()
            if not common_dictionary.__contains__(val):
                common_dictionary[val] = list()
            small_lst.append(assessment_type)
            small_lst.append(org_unit_name)
            common_dictionary[val].append(small_lst)

    return common_dictionary


def heat_map_data(webPage, survey_ID, token):
    """
    This function is responsible for getting all the data from the Unit_Questions API for
    the Heat Map for the Org_Unit_Questions
    :param webPage: The URL of the web page
    :param survey_ID:
    :param token: The token that will be sent as a header.
            Usually indicates that permission has been given to the given party or
            individual who is using the data.
    :return: A Tuple containing:
                0: A Tuple containing:
                    0: Categorical Names
                    1: ID
                1: Categorical Average
                2: A dictionary of category specific questions
                    :key (id): specific categorical id to match the
                            following questions
                    :value (text): text from the categorical specific questions

                3: A dictionary of category specific answers
                    :key (id): specific categorical id to match the
                            following questions
                    :value (answer): "answer" dictionary
    """

    response = r.get(webPage + "api/reports/" + survey_ID + "/unit_questions",
                     headers={"Authorization": "Token " + token, "Content-Type": "application/json"})

    data = json.loads(response.text)
    categories = data["categories"]
    questions = data["questions"]
    z_names = list()
    z_avg = list()
    z_text_questions = dict()
    z_answer_questions = dict()
    for dictionary in categories:
        z_names.append((dictionary["name"], dictionary["id"]))

        # for proper value representation on the Heat Map
        # The value will be represented on each cell.
        z_avg.append(round((dictionary["average"] / 100), 4))

        z_text_questions.setdefault(dictionary["id"], list())
        z_answer_questions.setdefault(dictionary["id"], list())

    for dictionary in questions:
        question = dictionary["question"]
        answer = dictionary["answer"]
        z_text_questions[question["category"]].append(question["text"])
        z_answer_questions[question["category"]].append(answer)

    return z_names, z_avg, z_text_questions, z_answer_questions


def getSurvey_ID(assessment_type, assessment_name, org_unit_name, token):
    """
    Function that is responsible to get the required survey_id of the given attributes. If the survey_id doesn't
    exist then 'Survey_ID does not EXIST' is given as the output.
    :param assessment_type: The type of the Assessment
    :param assessment_name: The name of the Assessment
    :param org_unit_name: The Org Unit Name
    :param token: The token that will be sent as a header.
            Usually indicates that permission has been given to the given party or
            individual who is using the data.
    :return: survey_id OR 'Survey_ID does not EXIST'
    """

    response = r.get("https://demo.isora.saltycloud.com/api/reports",
                     headers={"Authorization": "Token " + token,
                              "Content-Type": "application/json"})

    data = json.loads(response.text)
    results = data["results"]
    for dictionary in results:
        if dictionary["assessment_name"] == assessment_name and dictionary["assessment_type"] == assessment_type:
            if dictionary["org_unit_name"] == org_unit_name:
                return dictionary["survey_id"]

    return "Survey_ID does not EXIST"


if __name__ == '__main__':
    # print(getSurvey_ID("GLBA", "SaltyU SFA FY'18 - spring", "Infrastructure & Students",
    #                    "c548a5524615454ac53281ac01efd56bbf69f4d9"))

    dictionary = common_heat_map_data(getData("https://demo.isora.saltycloud.com/", "c548a5524615454ac53281ac01efd56bbf69f4d9"))

    heat_map_data("https://demo.isora.saltycloud.com/", "04e818ce-6d54-4ea0-a7ef-1c2bb2d52936",
                  "c548a5524615454ac53281ac01efd56bbf69f4d9")
