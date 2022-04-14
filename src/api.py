import requests as req

class Search:
    def __init__(self) -> None:
        self.url = "https://api.hh.ru/vacancies"
        self.counter = 5

    def get_vacancies(
        self,
        text: str,
        schedule: str,
        area: int,
        salary: int,
        only_with_salary: bool = True,
        currency="RUR",
    ) -> dict:
        params = {
            "text": f"NAME:({text})",
            "schedule": schedule,
            "area": area,
            "currency": currency,
            "salary": salary,
            "only_with_salary": only_with_salary,
        }
        filtered = {k: v for k, v in params.items() if v is not None}
        params.clear()
        params.update(filtered)
        response = req.get(self.url, params=params)
        if response.status_code == 200:
            print('happend!!')
            self.counter += 5
            vacancies = response.json()["items"][self.counter-5:self.counter]
            result = []
            for vacancy in vacancies:
                result.append({
                "id": vacancy["id"] if vacancy["id"] else "",
                "name": vacancy["name"] if vacancy["name"] else "",
                "url": vacancy["alternate_url"] if vacancy["alternate_url"] else "",
                "salary": vacancy["salary"] if vacancy["salary"] else {},
            })
            return result 
        print('LOX')
        
        return {"error": "Something went wrong"}

    def get_vacancy(self, vacancy_id: int) -> dict:
        response = req.get(f"{self.url}/{vacancy_id}")
        if response.status_code == 200:
            res_data = response.json()
            return {
                "name": res_data["name"] if res_data["name"] else "",
                "description": res_data["description"] if res_data["description"]else "",
                "branded_description": res_data["branded_description"] if res_data["branded_description"] else "",
                "url": res_data["alternate_url"] if res_data["alternate_url"] else "",
                "salary": res_data["salary"] if res_data["salary"] else {},
            }
        return {"error": "Something went wrong"}