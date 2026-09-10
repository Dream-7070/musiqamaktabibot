# state.py
#
# Handlerlar orasida bo'lishiladigan holat.

user_state = {}


TEACHER_DOCUMENTS = "teacher_documents"

STUDENT_DOCUMENTS = "student_documents"


class SelectedTeachers(dict):
    """
    Kim hozir qaysi o'qituvchi sifatida ishlayapti.

    Oddiy o'qituvchi uchun bu oddiy lug'at: kirganda o'z ismi
    yoziladi. Admin uchun esa haqiqat manbai - BAZA
    (`get_view_as`), xotira emas.

    Sababi: ko'rish rejimi Mini App'da o'chirilgan bo'lishi
    mumkin, bot esa boshqa jarayon - buni faqat bazadan biladi.
    Aks holda admin Mini App'da rejimdan chiqqach ham botda
    o'sha o'qituvchi menyusida qolib ketardi va tugmalar hamon
    uning nomidan ishlayverardi.

    `is_admin` va `get_view_as` tashqaridan beriladi - bu modul
    `config` va `database` ga bog'lanib qolmasligi uchun.
    """

    def __init__(self, is_admin, get_view_as):

        dict.__init__(self)

        self._is_admin = is_admin

        self._get_view_as = get_view_as

    def get(self, chat_id, default=None):

        if self._is_admin(chat_id) and self._get_view_as(chat_id) is None:

            dict.pop(self, chat_id, None)

            return default

        return dict.get(self, chat_id, default)

    def __getitem__(self, chat_id):

        value = self.get(chat_id)

        if value is None:
            raise KeyError(chat_id)

        return value

    def __contains__(self, chat_id):

        return self.get(chat_id) is not None
