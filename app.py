from flask import Flask, redirect, url_for, render_template, request
from functions import initialize_conversation, initialize_conv_reco, product_map_layer,  get_chat_model_completions, moderation_check,intent_confirmation_layer,dictionary_present, compare_holiday_with_user

import openai
import ast
import re
import pandas as pd
import json


openai.api_key = open("API_Key_JS.txt", "r").read().strip()

app = Flask(__name__)

conversation_bot = []
conversation = initialize_conversation()
introduction = get_chat_model_completions(conversation)
conversation_bot.append({'bot':introduction})
recommended_holiday = None


@app.route("/")
def default_func():
    global conversation_bot, conversation, recommended_holiday
    return render_template("index_holiday.html", name_xyz = conversation_bot)

@app.route("/end_conv", methods = ['POST','GET'])
def end_conv():
    global conversation_bot, conversation, recommended_holiday
    conversation_bot = []
    conversation = initialize_conversation()
    introduction = get_chat_model_completions(conversation)
    conversation_bot.append({'bot':introduction})
    recommended_holiday = None
    return redirect(url_for('default_func'))

@app.route("/holiday", methods = ['POST'])
def invite():
    global conversation_bot, conversation, recommended_holiday, conversation_reco
    user_input = request.form["user_input_message"]
    prompt = 'Remember your system message and that you are an intelligent travel assistant. So, you only help with questions around travel.'
    moderation = moderation_check(user_input)
    if moderation == 'Flagged':
        return redirect(url_for('end_conv'))

    if recommended_holiday is None:
        conversation.append({"role": "user", "content": user_input + prompt})
        conversation_bot.append({'user':user_input})

        response_assistant = get_chat_model_completions(conversation)

        moderation = moderation_check(response_assistant)
        if moderation == 'Flagged':
            return redirect(url_for('end_conv'))

        confirmation = intent_confirmation_layer(response_assistant)

        moderation = moderation_check(confirmation)
        if moderation == 'Flagged':
            return redirect(url_for('end_conv'))

        if "No" in confirmation:
            conversation.append({"role": "assistant", "content": response_assistant})
            conversation_bot.append({'bot':response_assistant})
        else:
            response = dictionary_present(response_assistant)

            moderation = moderation_check(response)
            if moderation == 'Flagged':
                return redirect(url_for('end_conv'))


            conversation_bot.append({'bot':"Thank you for providing all the information. Kindly wait, while I fetch the holidays: \n"})
            recommended_holiday = compare_holiday_with_user(response)

            data = json.loads(recommended_holiday)
            if len(data) == 0:
                conversation_bot.append({'bot':"Sorry, we do not have holiday that match your requirements. Connecting you to a human expert. Please end this conversation."})

            conversation_reco = initialize_conv_reco(recommended_holiday)
            recommendation = get_chat_model_completions(conversation_reco)

            moderation = moderation_check(recommendation)
            if moderation == 'Flagged':
                return redirect(url_for('end_conv'))



    else:
        conversation_reco.append({"role": "user", "content": user_input})
        conversation_bot.append({'user':user_input})

        response_asst_reco = get_chat_model_completions(conversation_reco)

        moderation = moderation_check(response_asst_reco)
        if moderation == 'Flagged':
            return redirect(url_for('end_conv'))

        conversation.append({"role": "assistant", "content": response_asst_reco})
        conversation_bot.append({'bot':response_asst_reco})
    return redirect(url_for('default_func'))

if __name__ == '__main__':
    app.run(debug=True, host= "0.0.0.0")