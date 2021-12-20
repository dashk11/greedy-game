import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class DataTree:
    def __init__(self, web_requests: int, time_spent: int,
                 dimensions={}, metrics={},
                 *args, **kwargs):
        self.web_requests = web_requests
        self.time_spent = time_spent
        self.dimensions = dimensions
        self.metrics = metrics
        self.additional_params = kwargs.get("additional_params", {})


class DataCollectionTree:
    def __init__(self):
        self.head = None

    def _get_metrics(self, metrics):
        for v in metrics:
            if v["key"] == "webreq":
                web_requests = v["val"]
            elif v["key"] == "timespent":
                time_spent = v["val"]
            else:
                print("Not valid metric")
        return web_requests, time_spent

    def _get_dimensions(self, dimensions):
        country, device = "", ""
        for v in dimensions:
            if v["key"] == "country":
                country = v["val"]
            elif v["key"] == "device":
                device = v["val"]
            else:
                print("Not valid dimension")
        return country, device

    def _upsert_dimensions(self, country, device, web_requests, time_spent):
        if self.head.dimensions.get(country) is not None:
            self.head.dimensions[country].web_requests += web_requests
            self.head.dimensions[country].time_spent += time_spent

            if self.head.dimensions[country].metrics.get(device) is not None:
                self.head.dimensions[country].metrics[device].web_requests += web_requests
                self.head.dimensions[country].metrics[device].time_spent += time_spent
            else:
                self.head.dimensions[country].metrics[device] = DataTree(web_requests=web_requests,
                                                                         time_spent=time_spent)

        else:
            self.head.dimensions[country] = DataTree(web_requests=web_requests,
                                                     time_spent=time_spent,
                                                     metrics={device: DataTree(web_requests=web_requests,
                                                                               time_spent=time_spent)})

    def insert(self, request):
        """ /v1/insert """
        web_requests, time_spent = self._get_metrics(
            metrics=request["metrics"])
        country, device = self._get_dimensions(dimensions=request["dim"])
        # print(f"""---{web_requests, time_spent, country, device}---""")
        if self.head is None:
            self.head = DataTree(web_requests=web_requests,
                                 time_spent=time_spent)
            self._upsert_dimensions(country, device, web_requests, time_spent)

            # print("---Inserted---")
        else:
            self.head.web_requests += web_requests
            self.head.time_spent += time_spent

            self._upsert_dimensions(country, device, web_requests, time_spent)

    def _display(self):
        res = {"web_requests": self.head.web_requests,
               "time_spent": self.head.time_spent,
               }
        for d in self.head.dimensions.keys():
            if res.get("dimensions") is None:
                res["dimensions"] = {}
            res["dimensions"][d] = {"web_requests": self.head.dimensions[d].web_requests,
                                    "time_spent": self.head.dimensions[d].time_spent,
                                    }

            for m in self.head.dimensions[d].metrics:
                # print(f"{d} -> {m}")
                if res["dimensions"][d].get("metrics") is None:
                    res["dimensions"][d]["metrics"] = {}
                res["dimensions"][d]["metrics"][m] = {"web_requests": self.head.dimensions[d].metrics[m].web_requests,
                                                      "time_spent": self.head.dimensions[d].metrics[m].time_spent}
        return res

    def query(self, request):
        """ /v1/query """
        print(request)
        if request.get("dim") is not None:
            country, device = self._get_dimensions(request["dim"])
            res = self._display()

            if res["dimensions"].get(country) is None:
                return f"No data exists for {country}"
            else:
                country_data = res["dimensions"][country]
                result = {"dim": [{"key": "country", "val": country}],
                          "metrics": []}
                for k, v in country_data.items():
                    if k != "metrics":
                        result["metrics"].append({"key": k, "val": v})
                return result
        else:
            return "No data available"


# Tree object in memory
TREE_OBJECT = None


class RetrieveTreeData(APIView):

    def get(self, request):
        global TREE_OBJECT
        r = request.data
        response = ""
        if TREE_OBJECT is not None:
            response = TREE_OBJECT.query(request=r)
            print(response)
        return Response({"response": response}, status=status.HTTP_200_OK)


class InsertTreeData(APIView):
    def post(self, request):
        global TREE_OBJECT
        insert = request.data
        if TREE_OBJECT is None:
            temp_obj = DataCollectionTree()
        else:
            temp_obj = TREE_OBJECT
        temp_obj.insert(request=insert)
        TREE_OBJECT = temp_obj
        response = {"response": "Inserted"}
        return Response({"data": response}, status=status.HTTP_200_OK)
