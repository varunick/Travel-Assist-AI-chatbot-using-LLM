import openai
import ast
import re
import pandas as pd
import json


def initialize_conversation():
    '''
        Returns a list [{"role": "system", "content": system_message}]
    '''

    delimiter = "####"
    example_user_req = {'Destination': 'Manali', 'Package': 'Deluxe', 'Origin': 'New Delhi', 'Duration': '4',
                        'Budget': '15000 INR'}

    system_message = f"""

        You are an intelligent holiday planner and your goal is to find the best holiday package for a user.
        You need to ask relevant questions and understand the user preferences by analysing the user's responses.
        You final objective is to fill the values for the different keys ('Destination','Package','Origin','Duration','Budget') in the python dictionary and be confident of the values.
        These key value pairs define the user's preference.
        The python dictionary looks like this {{'Destination': 'values','Package': 'values','Origin': 'values','Duration': 'values','Budget': 'values'}}

        The value for all the keys should be extracted from the user's response.
        The values currently in the dictionary are only representative values.

        {delimiter}Here are some instructions around the values for the different keys. If you do not follow this, you'll be heavily penalised.
        - The value for 'Budget' should be a numerical value extracted from the user's response.
        - 'Budget' value needs to be greater than or equal to 6500 INR. If the user says less than that, please mention that there are no holiday packages in that range.
        - The value for 'Duration' should be a numerical value extracted from the user's response.
        - 'Origin' value can either be 'Mumbai' or 'New Delhi'. If the user mentions any other city, please mention that we are travel company dealing in holidays only from Mumbai and New Delhi
        - For 'Package', give user the option whether they want to go for a 'Premium', 'Deluxe' , 'Luxury' or 'Standard' option.
        - Do not randomly assign values to any of the keys. The values need to be inferred from the user's response.
        {delimiter}

        To fill the dictionary, you need to have the following chain of thoughts:
        {delimiter} Thought 1: Ask a question to understand the user's preference for the holiday destination and number of nights. \n
        If their primary destination is unclear. Ask another question to comprehend their needs.
        You are trying to fill the values of all the keys ('Destination','Package','Origin','Duration','Budget') in the python dictionary by understanding the user requirements.
        Identify the keys for which you can fill the values confidently using the understanding. \n
        Remember the instructions around the values for the different keys.
        Answer "Yes" or "No" to indicate if you understand the requirements and have updated the values for the relevant keys. \n
        If yes, proceed to the next step. Otherwise, rephrase the question to capture their requirements. \n{delimiter}

        {delimiter}Thought 2: Now, you are trying to fill the values for the rest of the keys which you couldn't in the previous step.
        Remember the instructions around the values for the different keys. Ask questions you might have for all the keys to strengthen your understanding of the user's profile.
        Answer "Yes" or "No" to indicate if you understood all the values for the keys and are confident about the same.
        If yes, move to the next Thought. If no, ask question on the keys whose values you are unsure of. \n
        It is a good practice to ask question with a sound logic as opposed to directly citing the key you want to understand value for.{delimiter}

        {delimiter}Thought 3: Check if you have correctly updated the values for the different keys in the python dictionary.
        If you are not confident about any of the values, ask clarifying questions. {delimiter}

        Follow the above chain of thoughts and only output the final updated python dictionary. \n


        {delimiter} Here is a sample conversation between the user and assistant:
        User: "Hi, I want to visit Manali."
        Assistant: "Great! For what duration would you like to visit Manali"
        User: "I would like to visit for 4 nights."
        Assistant: "Thank you for providing that information. Which of the below package would you like to opt for:
        Standard
        Premium
        Deluxe
        Luxury"
        User: "I would like to go with Deluxe"
        Assistant: "Thank you for the information. Could you please let me know whether your origin city would be New Delhi or Mumbai?"
        User: "i'll start from New Delhi"
        Assistant:"Great, thanks. Could you kindly let me know your per person budget for the holiday package? This will help me find options that fit within your price range while meeting the specified requirements."
        User: "my max budget is 15000 inr"
        Assistant: "{example_user_req}"
        {delimiter}

        Start with a short welcome message and encourage the user to share their requirements.
        """
    conversation = [{"role": "system", "content": system_message}]
    return conversation


def get_chat_model_completions(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
        max_tokens = 2500
    )
    return response.choices[0].message["content"]



def moderation_check(user_input):
    response = openai.Moderation.create(input=user_input)
    moderation_output = response["results"][0]
    if moderation_output["flagged"] == True:
        return "Flagged"
    else:
        return "Not Flagged"


    
def intent_confirmation_layer(response_assistant):
    delimiter = "####"
    prompt = f"""
    You are a senior evaluator who has an eye for detail.
    You are provided an input. You need to evaluate if the input has the following keys: 'Destination','Package','Origin','Duration','Budget'
    Next you need to evaluate if the keys have the the values filled correctly.
    - The value for the key 'Budget' needs to contain a number with currency.
    - The value of key 'Package' needs to be either  'Premium', 'Deluxe' , 'Luxury' or 'Standard'
    - The value of key 'Duration' needs to contain a number
    - The value of key 'Origin' should either be 'New Delhi' or 'Mumbai'
    Output a string 'Yes' if the input contains the dictionary with the values correctly filled for all keys.
    Otherwise out the string 'No'.

    Here is the input: {response_assistant}
    Only output a one-word string - Yes/No.
    """


    confirmation = openai.Completion.create(
                                    model="text-davinci-003",
                                    prompt = prompt,
                                    temperature=0)


    return confirmation["choices"][0]["text"]




def dictionary_present(response):
    delimiter = "####"
    user_req = {'Destination': 'Manali','Package': 'Deluxe','Origin': 'New Delhi','Duration': '4','Budget': '15000 INR'}
    prompt = f"""You are a python expert. You are provided an input.
            You have to check if there is a python dictionary present in the string.
            It will have the following format {user_req}.
            Your task is to just extract and return only the python dictionary from the input.
            The output should match the format as {user_req}.
            The output should contain the exact keys and values as present in the input.

            Here are some sample input output pairs for better understanding:
            {delimiter}
            input: - Destination: Manali - Package: Luxury - Origin: Delhi - Duration: 4 - Budget: 50,000 INR
            output: {{'Destination': 'Manali', 'Package': 'Luxury', 'Origin': 'New Delhi', 'Duration': '4', 'Budget': '50000'}}

            input: {{'Destination':     'jaipur', 'Package':     'Standard', 'Origin':    'Mumbai', 'Duration': '4','Budget': '90,000'}}
            output: {{'Destination': 'Jaipur', 'Package': 'Standard', 'Origin': 'Mumbai', 'Duration': '4', 'Budget': '90000'}}

            input: Here is your user profile 'Destination': 'Ooty','Package': 'Deluxe','Origin': 'New Delhi','Duration': '5','Budget': '100000 INR'
            output: {{'Destination': 'Ooty', 'Package': 'Deluxe', 'Origin': 'New Delhi', 'Duration': '5', 'Budget': '100000'}}
            {delimiter}

            Here is the input {response}

            """
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens = 2000
        # temperature=0.3,
        # top_p=0.4
    )
    return response["choices"][0]["text"]



def extract_dictionary_from_string(string):
    regex_pattern = r"\{[^{}]+\}"

    dictionary_matches = re.findall(regex_pattern, string)

    # Extract the first dictionary match and convert it to lowercase
    if dictionary_matches:
        dictionary_string = dictionary_matches[0]
        dictionary_string = dictionary_string.lower()

        # Convert the dictionary string to a dictionary object using ast.literal_eval()
        dictionary = ast.literal_eval(dictionary_string)
    return dictionary


def product_map_layer(Destination, Package, Origin, Duration):
    delimiter = "#####"
    holiday_spec = {
        "Destination": "(Holiday destination)",
        "Package": "(Type of the holiday package)",
        "Origin": "(Origin city of the holiday)",
        "Duration": "(Maximum duration of the holiday)"

    }

    prompt = f"""
  You are a Holiday expert whose job is to extract the key features of a holiday package as per their requirements.
  Extract all the features above acccording to following rules: \
  {delimiter}
  Destination: Extract the first word until you find '|'. If there is only one word, extract the same from {Destination}

  Package: Extract the exact value from {Package} 

  Origin: Extract the exact value from {Origin}

  Duration: Add all the numbers you find and output the sum from {Duration}

  {delimiter}

  {delimiter}
  Here are some input output pairs for few-shot learning:
  input1: "Gangtok|Lachung|Gangtok|Darjeeling, Deluxe, New Delhi, 2N Gangtok . 2N Lachung . 1N Gangtok . 2N Darjeeling"
  output1: {{'Destination': 'Gangtok','Package':'Deluxe','Origin':'New Delhi','Duration':'7'}}

  input2: "Cochin|Munnar|Thekkady|Allepey|Kovalam and Poovar, Standard, Mumbai, 1N Cochin . 2N Munnar . 1N Thekkady . 1N Allepey . 2N Kovalam and Poovar"
  output2: {{'Destination': 'Cochin','Package':'Standard','Origin':'Mumbai','Duration':'7'}}

  input3: "Dharamshala, Deluxe, New Delhi, 3N Dharamshala"
  output3: {{'Destination': 'Dharamshala','Package':'Deluxe','Origin':'New Delhi','Duration':'3'}}
  {delimiter}

  Follow the above instructions step-by-step and output only the dictionary {holiday_spec} without any additional text for the following holiday package {Destination, Package, Origin, Duration}.
  """

    # see that we are using the Completion endpoint and not the Chatcompletion endpoint

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=2000,
        # temperature=0.3,
        # top_p=0.4
    )
    return response["choices"][0]["text"]


def compare_holiday_with_user(user_req_string):
    holiday_df = pd.read_csv('HolidayData2.csv')
    ## Create a new column "holiday_feature" that contains the dictionary of the product features
    holiday_df['holiday_feature'] = holiday_df.apply(lambda x: product_map_layer(x['Destination'], x['Package Type'], x['Start City'], x['Itinerary']), axis=1)

    # extract user requirements into a dictionary
    user_requirements = extract_dictionary_from_string(user_req_string)

    # This line retrieves the value associated with the key 'budget' from the user_requirements dictionary.
    # If the key is not found, the default value '0' is used.
    # The value is then processed to remove commas, split it into a list of strings, and take the first element of the list.
    # Finally, the resulting value is converted to an integer and assigned to the variable budget.
    budget = int(user_requirements.get('budget', '0').replace(',', '').split()[0])

    # filter filtered_holiday to include only rows where the 'Per Person Price' is less than or equal to the budget.
    filtered_holiday = holiday_df.copy()
    filtered_holiday = filtered_holiday[filtered_holiday['Per Person Price'] <= budget].copy()

    # delete budget key from user requirements before comparing with holiday package
    del user_requirements['budget']

    # extract holiday packages into a dictionary so that it can be compared with user requirements
    filtered_holiday['holiday_feature'] = filtered_holiday['holiday_feature'].apply(
        lambda x: extract_dictionary_from_string(x))

    # comparison of user requirements with holiday packages and returning the matching rows from df
    mask = filtered_holiday['holiday_feature'].apply(
        lambda x: all(x[key] == user_requirements[key] for key in user_requirements))
    result_df = filtered_holiday[mask]

    return result_df.to_json(orient='records')





def initialize_conv_reco(products):
    system_message = f"""
    You are an intelligent holiday expert and you are tasked with the objective to \
    solve the user queries about any product from the catalogue: {products}.\
    You should keep the user requirements in mind while answering the questions.\

    Start with a brief summary of each holiday in the following format, in decreasing order of price per person:
    1. <Holiday Name> : <Major attractions of the holiday>, <Price per person in Rs>
    2. <Holiday Name> : <Major attractions of the holiday>, <Price per person in Rs>

    """
    conversation = [{"role": "system", "content": system_message }]
    return conversation