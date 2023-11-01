# -*- coding: utf-8 -*-
"""pair_program_backend.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1kaa9VdJFefRg9J_HbrOuMygzehy_zqfL
"""

# Commented out IPython magic to ensure Python compatibility.
# %pip install "shapely<2.0.0" --quiet
# %pip install langchain --quiet
# %pip install google-cloud-aiplatform --upgrade --quiet
# %pip install gradio --quiet
# %pip install openai --quiet
# %pip install streamlit --quiet

from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models.vertexai import ChatVertexAI
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda
from langchain.memory import ConversationBufferMemory
import gradio as gr
import streamlit as st
import vertexai
import openai
import json

from google.colab import auth as google_auth
google_auth.authenticate_user()

vertexai.init(project="project-radicalx", location="us-central1")

intent_chain = PromptTemplate.from_template('''You are helping a user solve a coding problem, provided below.

Given the user message, classify its intent as one of the following categories: `asking for problem solving strategy`, `asking for review of user's code`, `general Python question`, `other`.

Respond with the topic only and no other words.

<coding_problem>
{coding_problem}
</coding_problem>

<message>
{message}
</message>

Classification''') | ChatVertexAI() | StrOutputParser()

collab_chain = ChatPromptTemplate.from_messages([
    ('system', '''You are working with a user on their Python problem, provided below. They have also written some code. Assume you don't know how to solve the problem.

Please comment on the user message, using emojis where appropriate. If the user talks about their code, please take a look at their code as well. Be vague - don't give any big hints, next steps, solutions, or the answer.

If you give a hint, only give a single step do not give all the steps at once.

Keep your response 1-2 sentences maximum. Remember - talk like you are a coding partner and not the user's teacher. Don't give any code.

<coding_problem>
{coding_problem}
</coding_problem>

<user_code>
{user_code}
</user_code>

<code_output>
{code_output}
</code_output>'''),
    MessagesPlaceholder(variable_name='chat_history'),
    ('human', '{message}')]) | ChatVertexAI()

code_chain = ChatPromptTemplate.from_messages([
    ('system', '''You are working with a user on their Python problem, provided below. They have also written some code. Assume you don't know how to solve the problem.

Please provide a small snippet of code relevant to the user message. Keep it short and to the point. Don't give any hints, solutions, or the answer.

Use emojis where appropriate. Remember - talk like you are a coding partner and not the user's teacher.

<coding_problem>
{coding_problem}
</coding_problem>

<user_code>
{user_code}
</user_code>'''),
    MessagesPlaceholder(variable_name='chat_history'),
    ('human', '{message}')]) | ChatVertexAI()

default_chain = ChatPromptTemplate.from_messages([
    ('system', '''You are a junior coder helping a user solve a Python coding problem. Reply back to the user's message using plenty of appropriate emojis.

Keep your answer short and to the point. Don't ask follow-up questions.'''),
    MessagesPlaceholder(variable_name='chat_history'),
    ('human', '{message}')]) | ChatVertexAI()

def response_route(info):
  if 'asking for problem solving strategy' in info['intent'].lower():
      return 'STRATEGY\n' + str(collab_chain.invoke(info).content)
      #return str(collab_chain.invoke(info).content)
  elif f'''asking for review of user's code''' in info['intent'].lower():
      return f'''Sounds like you're asking me for a code review/debug'''
  elif 'general Python question' in info['intent'].lower():
      return 'GENERAL CODING\n' + str(code_chain.invoke(info).content)
      #return str(code_chain.invoke(info).content)
  else:
      return 'DEFAULT\n' + str(default_chain.invoke(info).content)
      #return str(default_chain.invoke(info).content)

response_chain = {
    'intent': intent_chain,
    'message': lambda x: x['message'],
    'coding_problem': lambda x: x['coding_problem'],
    'user_code': lambda x: x['user_code'],
    'code_output': lambda x: x['code_output'],
    'chat_history': lambda x: x['chat_history']
} | RunnableLambda(response_route)

screen_chain = PromptTemplate.from_template('''A coding problem is provided below, as 'coding problem'.

Given 'response', determine if 'response' meets any of the following criteria:

- Gives the solution to 'coding problem'
- Not just a small hint, but gives the whole strategy for solving 'coding problem'
- Providing code to specifically solve 'coding problem'

Small talk is fine. Respond with a single character, either 'Y' for yes or 'N' for no.

<coding_problem>
{coding_problem}
</coding_problem>

<response>
{response}
</response>

Classification''') | ChatVertexAI() | StrOutputParser()

def output_route(info):
  if 'n' in info['screen'].lower():
      return info['response']
  elif 'y' in info['screen'].lower():
      #debug_msg = 'SCREENED OUT\n' + info['response'] + '\n'
      debug_msg = ''
      return debug_msg + f'''I'm sorry, I don't have a good response to that. You can say it in a different way or tell me something else :)'''
  else:
      return 'There was an error with the output screening'

output_chain = {
    'screen': screen_chain,
    'message': lambda x: x['message'],
    'coding_problem': lambda x: x['coding_problem'],
    'response': lambda x: x['response'],
} | RunnableLambda(output_route)

#API Key
OPENAI_API_KEY="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"
openai.api_key=OPENAI_API_KEY

def get_coding_problem():
  #Prompt Template
  prompt_template = f"""
  Please generate a coding question with one test input.
  Format your response as a JSON object with the following 2 keys:

  "Description": A text description of the coding question
  "Input": This should contain a dictionary where the key-value pairs are test input variable names and their values

  Do not include any additional information like examples, outputs, hints.
  """

  #Response
  response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=prompt_template,
      max_tokens=1024,
      n=1,
      stop=None,
      temperature=1,
  )

  return response["choices"][0]["text"]

# lookup = json.loads(get_coding_problem())

# prob_description = lookup['Description']
# prob_inputs = ''

# for var_name, var_val in lookup['Input'].items():
#   prob_inputs += f'''{var_name} = {var_val}\n'''

# print(prob_description)
# print(prob_inputs)

lookup = json.loads(get_coding_problem())

prob_description = lookup['Description']
prob_inputs = ''

for var_name, var_val in lookup['Input'].items():
  prob_inputs += f'''{var_name} = {var_val}\n'''

global coding_problem
coding_problem = f'''
Description:
{prob_description}

Inputs:
{prob_inputs}
'''

memory = ConversationBufferMemory(return_messages=True)
memory.save_context({'input': f'''Let's practice coding in Python.'''}, {'output': f'''Let's do it! Here's a problem that I found:\n{coding_problem}'''})

with gr.Blocks() as demo:

  def get_completion(msg, user_code, code_output, script):
    global coding_problem

    response_inputs = {'coding_problem': coding_problem, 'message': msg, 'user_code': user_code, 'code_output': code_output, 'chat_history': memory.load_memory_variables({})['history']}
    response = response_chain.invoke(response_inputs)
    output = output_chain.invoke({'coding_problem': coding_problem, 'message': msg, 'response': response})

    memory.save_context({'input': msg}, {'output': output})
    script.append((msg, output))

    return '', script

  def run_code(code):
    try:
        local_vars = {}
        exec(code, None, local_vars)

        out_string = 'Your code ran successfully!\n'
        for var, val in local_vars.items():
            out_string += f'''\n{var} = {val}'''

        return out_string

    except Exception as e:
        return 'ERROR\n' + str(e)

  with gr.Row():
    with gr.Column():
      chatbot = gr.Chatbot([(f'''Let's practice coding in Python.''', f'''Let's do it! Here's a problem that I found:\n{coding_problem}''')])
      chat_input = gr.Textbox(value='', label='Chat with junior coder')

    with gr.Column():
      code = gr.Code(prob_inputs)
      code_submit = gr.Button(value='Run')
      code_output = gr.Textbox(value='', label='Code Output')

  chat_input.submit(get_completion, [chat_input, code, code_output, chatbot], [chat_input, chatbot])
  code_submit.click(run_code, [code], [code_output])

demo.launch()

"""**STREAMLIT**"""

coding_area=st.text_area("Coding Area")
output=st.text_area("Output")
solution=st.text_area("Solution")
# Just add it after st.sidebar:

with st.sidebar.chat_message("user"):
    a=st.sidebar.text_area("Hello, I am your Coding Companion. How Can I help!!👋",)

st.write(f'You wrote {len(output)} characters.')

! streamlit run /usr/local/lib/python3.10/dist-packages/colab_kernel_launcher.py