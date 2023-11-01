{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "provenance": [],
      "include_colab_link": true
    },
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/Ja1Pat3L/RadicalX_Challenge2/blob/main/Pair_Program_Backend.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {
        "id": "YIRItwu0yap1"
      },
      "outputs": [],
      "source": [
        "!pip install \"shapely<2.0.0\"\n",
        "!pip install langchain\n",
        "!pip install google-cloud-aiplatform --upgrade\n",
        "!pip install gradio\n",
        "!pip install openai"
      ]
    },
    {
      "cell_type": "code",
      "source": [
        "import vertexai\n",
        "from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder\n",
        "from langchain.chat_models.vertexai import ChatVertexAI\n",
        "from langchain.schema.output_parser import StrOutputParser\n",
        "from langchain.schema.runnable import RunnableLambda\n",
        "from langchain.memory import ConversationBufferMemory\n",
        "import gradio as gr\n",
        "import openai\n",
        "import json"
      ],
      "metadata": {
        "id": "exLERtQTye5H"
      },
      "execution_count": 2,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "from google.colab import auth as google_auth\n",
        "google_auth.authenticate_user()"
      ],
      "metadata": {
        "id": "KVJznCsDz2LT"
      },
      "execution_count": 3,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "vertexai.init(project=\"project-radicalx\", location=\"us-central1\")"
      ],
      "metadata": {
        "id": "PnV0kJlKz3rX"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "intent_chain = PromptTemplate.from_template('''You are helping a user solve a coding problem, provided below.\n",
        "\n",
        "Given the user message, classify its intent as one of the following categories: `asking for problem solving strategy`, `asking for review of user's code`, `general Python question`, `other`.\n",
        "\n",
        "Respond with the topic only and no other words.\n",
        "\n",
        "<coding_problem>\n",
        "{coding_problem}\n",
        "</coding_problem>\n",
        "\n",
        "<message>\n",
        "{message}\n",
        "</message>\n",
        "\n",
        "Classification''') | ChatVertexAI() | StrOutputParser()\n",
        "\n",
        "collab_chain = ChatPromptTemplate.from_messages([\n",
        "    ('system', '''You are working with a user on their Python problem, provided below. They have also written some code. Assume you don't know how to solve the problem.\n",
        "\n",
        "Please comment on the user message, using emojis where appropriate. If the user talks about their code, please take a look at their code as well. Be vague - don't give any big hints, next steps, solutions, or the answer.\n",
        "\n",
        "If you give a hint, only give a single step do not give all the steps at once.\n",
        "\n",
        "Keep your response 1-2 sentences maximum. Remember - talk like you are a coding partner and not the user's teacher. Don't give any code.\n",
        "\n",
        "<coding_problem>\n",
        "{coding_problem}\n",
        "</coding_problem>\n",
        "\n",
        "<user_code>\n",
        "{user_code}\n",
        "</user_code>\n",
        "\n",
        "<code_output>\n",
        "{code_output}\n",
        "</code_output>'''),\n",
        "    MessagesPlaceholder(variable_name='chat_history'),\n",
        "    ('human', '{message}')]) | ChatVertexAI()\n",
        "\n",
        "code_chain = ChatPromptTemplate.from_messages([\n",
        "    ('system', '''You are working with a user on their Python problem, provided below. They have also written some code. Assume you don't know how to solve the problem.\n",
        "\n",
        "Please provide a small snippet of code relevant to the user message. Keep it short and to the point. Don't give any hints, solutions, or the answer.\n",
        "\n",
        "Use emojis where appropriate. Remember - talk like you are a coding partner and not the user's teacher.\n",
        "\n",
        "<coding_problem>\n",
        "{coding_problem}\n",
        "</coding_problem>\n",
        "\n",
        "<user_code>\n",
        "{user_code}\n",
        "</user_code>'''),\n",
        "    MessagesPlaceholder(variable_name='chat_history'),\n",
        "    ('human', '{message}')]) | ChatVertexAI()\n",
        "\n",
        "default_chain = ChatPromptTemplate.from_messages([\n",
        "    ('system', '''You are a junior coder helping a user solve a Python coding problem. Reply back to the user's message using plenty of appropriate emojis.\n",
        "\n",
        "Keep your answer short and to the point. Don't ask follow-up questions.'''),\n",
        "    MessagesPlaceholder(variable_name='chat_history'),\n",
        "    ('human', '{message}')]) | ChatVertexAI()"
      ],
      "metadata": {
        "id": "ZtU1wRE1ztDp"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "def response_route(info):\n",
        "  if 'asking for problem solving strategy' in info['intent'].lower():\n",
        "      return 'STRATEGY\\n' + str(collab_chain.invoke(info).content)\n",
        "      #return str(collab_chain.invoke(info).content)\n",
        "  elif f'''asking for review of user's code''' in info['intent'].lower():\n",
        "      return f'''Sounds like you're asking me for a code review/debug'''\n",
        "  elif 'general Python question' in info['intent'].lower():\n",
        "      return 'GENERAL CODING\\n' + str(code_chain.invoke(info).content)\n",
        "      #return str(code_chain.invoke(info).content)\n",
        "  else:\n",
        "      return 'DEFAULT\\n' + str(default_chain.invoke(info).content)\n",
        "      #return str(default_chain.invoke(info).content)\n",
        "\n",
        "response_chain = {\n",
        "    'intent': intent_chain,\n",
        "    'message': lambda x: x['message'],\n",
        "    'coding_problem': lambda x: x['coding_problem'],\n",
        "    'user_code': lambda x: x['user_code'],\n",
        "    'code_output': lambda x: x['code_output'],\n",
        "    'chat_history': lambda x: x['chat_history']\n",
        "} | RunnableLambda(response_route)"
      ],
      "metadata": {
        "id": "pG-3uunt-38H"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "screen_chain = PromptTemplate.from_template('''A coding problem is provided below, as 'coding problem'.\n",
        "\n",
        "Given 'response', determine if 'response' meets any of the following criteria:\n",
        "\n",
        "- Gives the solution to 'coding problem'\n",
        "- Not just a small hint, but gives the whole strategy for solving 'coding problem'\n",
        "- Providing code to specifically solve 'coding problem'\n",
        "\n",
        "Small talk is fine. Respond with a single character, either 'Y' for yes or 'N' for no.\n",
        "\n",
        "<coding_problem>\n",
        "{coding_problem}\n",
        "</coding_problem>\n",
        "\n",
        "<response>\n",
        "{response}\n",
        "</response>\n",
        "\n",
        "Classification''') | ChatVertexAI() | StrOutputParser()\n",
        "\n",
        "def output_route(info):\n",
        "  if 'n' in info['screen'].lower():\n",
        "      return info['response']\n",
        "  elif 'y' in info['screen'].lower():\n",
        "      #debug_msg = 'SCREENED OUT\\n' + info['response'] + '\\n'\n",
        "      debug_msg = ''\n",
        "      return debug_msg + f'''I'm sorry, I don't have a good response to that. You can say it in a different way or tell me something else :)'''\n",
        "  else:\n",
        "      return 'There was an error with the output screening'\n",
        "\n",
        "output_chain = {\n",
        "    'screen': screen_chain,\n",
        "    'message': lambda x: x['message'],\n",
        "    'coding_problem': lambda x: x['coding_problem'],\n",
        "    'response': lambda x: x['response'],\n",
        "} | RunnableLambda(output_route)"
      ],
      "metadata": {
        "id": "NNCYJ762JXCq"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "#API Key\n",
        "OPENAI_API_KEY=\"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\"\n",
        "openai.api_key=OPENAI_API_KEY\n",
        "\n",
        "def get_coding_problem():\n",
        "  #Prompt Template\n",
        "  prompt_template = f\"\"\"\n",
        "  Please generate a coding question with one test input.\n",
        "  Format your response as a JSON object with the following 2 keys:\n",
        "\n",
        "  \"Description\": A text description of the coding question\n",
        "  \"Input\": This should contain a dictionary where the key-value pairs are test input variable names and their values\n",
        "\n",
        "  Do not include any additional information like examples, outputs, hints.\n",
        "  \"\"\"\n",
        "\n",
        "  #Response\n",
        "  response = openai.Completion.create(\n",
        "      engine=\"text-davinci-003\",\n",
        "      prompt=prompt_template,\n",
        "      max_tokens=1024,\n",
        "      n=1,\n",
        "      stop=None,\n",
        "      temperature=1,\n",
        "  )\n",
        "\n",
        "  return response[\"choices\"][0][\"text\"]"
      ],
      "metadata": {
        "id": "AFMF58JJoOOH"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "# lookup = json.loads(get_coding_problem())\n",
        "\n",
        "# prob_description = lookup['Description']\n",
        "# prob_inputs = ''\n",
        "\n",
        "# for var_name, var_val in lookup['Input'].items():\n",
        "#   prob_inputs += f'''{var_name} = {var_val}\\n'''\n",
        "\n",
        "# print(prob_description)\n",
        "# print(prob_inputs)"
      ],
      "metadata": {
        "id": "HENy9j0BpA4i"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "lookup = json.loads(get_coding_problem())\n",
        "\n",
        "prob_description = lookup['Description']\n",
        "prob_inputs = ''\n",
        "\n",
        "for var_name, var_val in lookup['Input'].items():\n",
        "  prob_inputs += f'''{var_name} = {var_val}\\n'''\n",
        "\n",
        "global coding_problem\n",
        "coding_problem = f'''\n",
        "Description:\n",
        "{prob_description}\n",
        "\n",
        "Inputs:\n",
        "{prob_inputs}\n",
        "'''\n",
        "\n",
        "memory = ConversationBufferMemory(return_messages=True)\n",
        "memory.save_context({'input': f'''Let's practice coding in Python.'''}, {'output': f'''Let's do it! Here's a problem that I found:\\n{coding_problem}'''})\n",
        "\n",
        "with gr.Blocks() as demo:\n",
        "\n",
        "  def get_completion(msg, user_code, code_output, script):\n",
        "    global coding_problem\n",
        "\n",
        "    response_inputs = {'coding_problem': coding_problem, 'message': msg, 'user_code': user_code, 'code_output': code_output, 'chat_history': memory.load_memory_variables({})['history']}\n",
        "    response = response_chain.invoke(response_inputs)\n",
        "    output = output_chain.invoke({'coding_problem': coding_problem, 'message': msg, 'response': response})\n",
        "\n",
        "    memory.save_context({'input': msg}, {'output': output})\n",
        "    script.append((msg, output))\n",
        "\n",
        "    return '', script\n",
        "\n",
        "  def run_code(code):\n",
        "    try:\n",
        "        local_vars = {}\n",
        "        exec(code, None, local_vars)\n",
        "\n",
        "        out_string = 'Your code ran successfully!\\n'\n",
        "        for var, val in local_vars.items():\n",
        "            out_string += f'''\\n{var} = {val}'''\n",
        "\n",
        "        return out_string\n",
        "\n",
        "    except Exception as e:\n",
        "        return 'ERROR\\n' + str(e)\n",
        "\n",
        "  with gr.Row():\n",
        "    with gr.Column():\n",
        "      chatbot = gr.Chatbot([(f'''Let's practice coding in Python.''', f'''Let's do it! Here's a problem that I found:\\n{coding_problem}''')])\n",
        "      chat_input = gr.Textbox(value='', label='Chat with junior coder')\n",
        "\n",
        "    with gr.Column():\n",
        "      code = gr.Code(prob_inputs)\n",
        "      code_submit = gr.Button(value='Run')\n",
        "      code_output = gr.Textbox(value='', label='Code Output')\n",
        "\n",
        "  chat_input.submit(get_completion, [chat_input, code, code_output, chatbot], [chat_input, chatbot])\n",
        "  code_submit.click(run_code, [code], [code_output])\n",
        "\n",
        "demo.launch()"
      ],
      "metadata": {
        "id": "U1knO1GkEN0E"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [],
      "metadata": {
        "id": "-_T6XvoGs92n"
      },
      "execution_count": null,
      "outputs": []
    }
  ]
}