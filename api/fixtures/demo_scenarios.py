"""Pre-baked demo scenarios for the live remediation feature.

Each scenario defines a known bug in the Online Boutique codebase
along with the alert and log evidence the agent uses to find it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DemoScenario:
    id: str
    title: str
    service: str
    severity: str
    language: str
    file_path: str
    description: str
    alert: dict
    logs: list[str] = field(default_factory=list)

    @property
    def branch_prefix(self) -> str:
        return f"parakeet-fix/{self.id}"

    def branch_name(self, incident_id: str) -> str:
        return f"parakeet-fix/{self.id}-{incident_id}"


SCENARIOS: dict[str, DemoScenario] = {
    # ---- Scenario 1: Go — shipping always $8.99 ----
    #
    # Online Boutique source locations:
    #   src/shippingservice/main.go    ~line 119  GetQuote() handler
    #     → line 124: calls CreateQuoteFromCount(0) — hardcoded 0 ignores
    #       len(in.Items), so every cart gets the same quote.
    #   src/shippingservice/quote.go   ~line 34   CreateQuoteFromCount()
    #     → ignores `count` param entirely, delegates to CreateQuoteFromFloat(8.99)
    #
    # The agent should find main.go via the "[GetQuote]" log prefix,
    # then trace the bug to the hardcoded 0 argument.
    "shipping-bug": DemoScenario(
        id="shipping-bug",
        title="Flat-Rate Shipping Bug",
        service="shippingservice",
        severity="P2",
        language="go",
        file_path="src/shippingservice/main.go",
        description="All shipping quotes return $8.99 regardless of cart size. "
        "The GetQuote handler passes a hardcoded 0 to CreateQuoteFromCount instead of the actual item count.",
        alert={
            "source": "Prometheus",
            "service": "shippingservice",
            "environment": "production",
            "metric": "shipping_cost_variance",
            "value": "0%",
            "threshold": ">5%",
            "message": "Shipping cost anomaly — all orders charged $8.99 regardless of cart size. "
            "Expected variance based on item count, but every quote returns the same amount.",
        },
        logs=[
            "INFO  shippingservice [GetQuote] received request",
            "INFO  shippingservice [GetQuote] completed request",
            "INFO  shippingservice [GetQuote] received request",
            "INFO  shippingservice [GetQuote] completed request",
            "WARN  monitoring  shipping_cost_variance=0% over last 1h — "
            "all 1,247 quotes returned $8.99 regardless of item count (range: 1-18 items)",
            "INFO  shippingservice [ShipOrder] received request",
            "INFO  shippingservice [ShipOrder] completed request",
        ],
    ),
    # ---- Scenario 2: Node.js — currency conversion failures ----
    #
    # Online Boutique source locations:
    #   src/currencyservice/server.js  ~line 138  convert() handler
    #     → line 146: data[from.currency_code] — no validation that
    #       from.currency_code exists in the data map. If it's missing,
    #       division by undefined produces NaN, then accessing .units on
    #       the carry result throws TypeError.
    #     → line 109: _getCurrencyData() loads currency_conversion.json
    #     → line 128: getSupportedCurrencies() returns valid codes
    #
    # The agent should find server.js from "currencyservice" + "convert"
    # in the error logs, then spot the missing validation before the
    # data[from.currency_code] lookup.
    "currency-bug": DemoScenario(
        id="currency-bug",
        title="Currency Conversion Failures",
        service="currencyservice",
        severity="P1",
        language="javascript",
        file_path="src/currencyservice/server.js",
        description="34% of currency conversion requests fail with TypeError. "
        "The convert function accesses data[from.currency_code] without validation, "
        "causing crashes on unsupported currency codes.",
        alert={
            "source": "Datadog",
            "service": "currencyservice",
            "environment": "production",
            "metric": "error_rate_5xx",
            "value": "34%",
            "threshold": "<1%",
            "message": "Error rate spike on currencyservice — 34% of conversion "
            "requests returning 5xx. TypeError in convert handler.",
        },
        logs=[
            "INFO  currencyservice Getting supported currencies...",
            "ERROR currencyservice conversion request failed: TypeError: Cannot read properties "
            "of undefined (reading 'units')",
            "ERROR currencyservice conversion request failed: TypeError: Cannot read properties "
            "of undefined (reading 'units')",
            "INFO  currencyservice Getting supported currencies...",
            "ERROR currencyservice conversion request failed: TypeError: Cannot read properties "
            "of undefined (reading 'units')",
            "WARN  monitoring  currencyservice error_rate=34% (threshold 1%) — "
            "all failures are TypeError in convert() when from.currency_code not in data map",
        ],
    ),
    # ---- Scenario 3: Python — recommendation crash ----
    #
    # Online Boutique source locations:
    #   src/recommendationservice/recommendation_server.py  ~line 70
    #     ListRecommendations() handler
    #     → line 75: filtered_products = list(set(product_ids) - set(request.product_ids))
    #       removes products already in the user's cart
    #     → line 79: random.sample(range(num_products), num_return)
    #       crashes with ValueError when num_products is 0 (empty filtered list),
    #       because random.sample() rejects sampling from an empty range.
    #
    # The agent should find recommendation_server.py from the
    # "ListRecommendations" and "ValueError: Sample larger than population"
    # log entries, then spot the missing empty-list guard before random.sample().
    "recommendation-bug": DemoScenario(
        id="recommendation-bug",
        title="Recommendation Crash on Full Cart",
        service="recommendationservice",
        severity="P2",
        language="python",
        file_path="src/recommendationservice/recommendation_server.py",
        description="Recommendation service crashes with ValueError when a user's cart "
        "contains all available products. random.sample() is called without checking "
        "for an empty filtered product list.",
        alert={
            "source": "Prometheus",
            "service": "recommendationservice",
            "environment": "production",
            "metric": "error_rate_5xx",
            "value": "12%",
            "threshold": "<1%",
            "message": "5xx error rate spike on recommendationservice — 12% of "
            "ListRecommendations requests failing with ValueError.",
        },
        logs=[
            "INFO  recommendationservice [Recv ListRecommendations] product_ids=[]",
            "ERROR recommendationservice ValueError: Sample larger than population or is negative",
            "INFO  recommendationservice [Recv ListRecommendations] product_ids=['OLJCESPC7Z']",
            "INFO  recommendationservice [Recv ListRecommendations] product_ids=[]",
            "ERROR recommendationservice ValueError: Sample larger than population or is negative",
            "WARN  monitoring  recommendationservice error_rate=12% — all failures are "
            "ValueError in ListRecommendations when filtered_products is empty after "
            "removing products already in cart",
        ],
    ),
}
