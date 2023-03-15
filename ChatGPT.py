import openai
import mtranslate
import logging

class ChatGPT:
    # Добавляем логирование в файл
    logging.basicConfig(level=logging.INFO, filename="logs.log",filemode="w")

    # Список ключей Open AI
    api_keys_list = []
    # Количество удаленных ключей
    removed_keys = 0

    # Функция инициализации объекта
    # api_keys - список с ключами
    def __init__(self, api_keys = []):
        # Сохраняем список переданных ключей
        self.api_keys_list = api_keys
        # Задаём текущий ключ Open AI
        openai.api_key = api_keys[0]
        # Инициализируем переменную для хранения истории диалога
        self.conversation_history = []

    # Функция отправки сообщения на сервера Open AI и получение ответа
    def getAnswer(self, message, lang="ru", max_tokens=1000, temperature=0.9, top_p=1, frequency_penalty=0.5, presence_penalty=0.5, engine_model="gpt-4"):
        i = 0
        errors = False
        message = mtranslate.translate(message, "en", "auto")

        # Добавляем текущее сообщение в историю диалога
        self.conversation_history.append(message)

        while(True):
            try:
                # Считаем количество токенов
                num_tokens = len(list(message))
                # Если количество токенов превышает допустимое количество, то возвращаем сообщение с ошибкой
                if(num_tokens > max_tokens):
                    errors = True
                    return {"message": mtranslate.translate("❌ You have exceeded the limit on the number of tokens. Please shorten your message.", lang, "auto"), "list_keys":self.api_keys_list, "attempts":i, "errors":errors, "num_tokens":num_tokens}

                # Отправляем текст на серверы OpenAI и получаем ответ
                response = openai.Completion.create(
                    engine=engine_model,
                    prompt='\n'.join(self.conversation_history),
                    max_tokens=max_tokens,
                    top_p=top_p,
                    temperature=temperature,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty
                )

                # Формируем результат ответа
                result = response["choices"][0]["text"].strip()

                # Если бот вернул пустой ответ
                if(not result):
                    errors = True
                    result = "❌ Sorry, the bot didn't return the result."

                # Добавляем ответ в историю диалога
                self.conversation_history.append(result)

                # Возращаем результат работы
                return {"message": mtranslate.translate(result, lang, "auto"), "list_keys":self.api_keys_list, "attempts":i, "errors":errors, "num_tokens":num_tokens}
            except Exception as e:
                # Если на аккаунте Chat GPT закончилась квота, меням ключ
                if "You exceeded your current quota" in str(e):
                    if(self.RemoveKey()):
                        return {"message": mtranslate.translate("❌ I'm sorry, but an unexpected error has occurred", lang, "auto"), "list_keys":self.api_keys_list, "attempts":i, "errors":errors, "num_tokens":num_tokens}
                else:
                    i += 1
                    

    # Функция удаления ключа из списка
    def RemoveKey(self):
        if(len(self.api_keys_list) > 1):
            self.api_keys_list.remove(self.api_keys_list[0])
            openai.api_key = self.api_keys_list[0]
            return False
        elif(len(self.api_keys_list) > 0):
            self.api_keys_list.remove(self.api_keys_list[0])
            return True
        return True