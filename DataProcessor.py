class DataProcessor:
    def __init__(self, data: list[dict[str, str | None]]):
        self.data = data

    def filter_by_category(self, data: list[dict[str, str | None]], category: str) -> list[dict[str, str | None]]:
        return [item for item in data if item.get('category') == category]

    def filter_by_city(self, data: list[dict[str, str | None]], city_name: str) -> list[dict[str, str | None]]:
        if city_name == "Вся Україна":
            return data
        return [item for item in data if item.get('Місто:') == city_name]

    def filter_by_age(self, data: list[dict[str, str | None]], max_age: str) -> list[dict[str, str | None]]:
        max_age = int(max_age)
        filtered_data = []
        for item in data:
            age_str = item.get('Вік', '').replace('\xa0', ' ').replace(' років', '').strip()
            try:
                age = int(age_str)
                if age <= max_age:
                    filtered_data.append(item)
            except ValueError:
                continue
        return filtered_data

    def apply_filters(self, category: str = None, city_name: str = None, max_age: str = None) -> list[dict[str, str | None]]:
        filtered_data = self.data

        if category:
            filtered_data = self.filter_by_category(filtered_data, category)

        if city_name:
            filtered_data = self.filter_by_city(filtered_data, city_name)

        if max_age:
            filtered_data = self.filter_by_age(filtered_data, max_age)

        return filtered_data

