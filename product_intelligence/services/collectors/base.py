from abc import ABC, abstractmethod


class BaseMarketCollector(ABC):
    source_name = None

    REQUIRED_FIELDS = {
        "source",
        "external_id",
        "name",
        "observed_price",
        "currency",
        "product_url",
        "image_url",
        "raw_data",
    }

    @abstractmethod
    def collect(self, query):
        raise NotImplementedError

    def validate_observation(self, observation):
        missing_fields = (
            self.REQUIRED_FIELDS
            - set(observation.keys())
        )

        if missing_fields:
            raise ValueError(
                (
                    "Observation invalide. "
                    f"Champs manquants : "
                    f"{sorted(missing_fields)}"
                )
            )

        if not observation["source"]:
            raise ValueError(
                "La source est obligatoire."
            )

        if not observation["external_id"]:
            raise ValueError(
                "L'identifiant externe est obligatoire."
            )

        if not observation["name"]:
            raise ValueError(
                "Le nom du produit est obligatoire."
            )

        return observation

    def validate_results(self, results):
        for observation in results:
            self.validate_observation(
                observation
            )

        return results
        