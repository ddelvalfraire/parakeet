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
        description=(
            "All shipping quotes return $8.99 regardless of cart size. "
            "The GetQuote handler passes a hardcoded 0 to "
            "CreateQuoteFromCount instead of the actual item count."
        ),
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
    # ---- Scenario 2: Node.js — currency conversion silent corruption ----
    #
    # Online Boutique source locations:
    #   src/currencyservice/server.js  ~line 138  convert() handler
    #     → data[from.currency_code] — no validation that the key exists.
    #       When the currency code is not in currency_conversion.json,
    #       data[code] returns undefined.  Division by undefined produces
    #       NaN, which propagates through _carry() and Math.floor().
    #       Proto serialization coerces NaN int fields to 0, so the gRPC
    #       client receives Money{units:0, nanos:0} — a silent $0.00.
    #     → The try/catch IS effective (callback is synchronous via
    #       require()), but no error is thrown — NaN arithmetic is silent.
    #       The app logs "conversion request successful" for every call.
    #     → _getCurrencyData() loads ./data/currency_conversion.json
    #     → getSupportedCurrencies() returns Object.keys(data)
    #
    # The agent should find server.js from the monitoring anomaly alert,
    # then trace the NaN propagation to the missing key validation.
    "currency-bug": DemoScenario(
        id="currency-bug",
        title="Currency Conversion Failures",
        service="currencyservice",
        severity="P1",
        language="javascript",
        file_path="src/currencyservice/server.js",
        description=(
            "34% of currency conversions silently return $0.00. "
            "The convert() function divides by "
            "data[from.currency_code] without checking the key "
            "exists — unsupported codes yield undefined, producing "
            "NaN that proto serialization coerces to zero."
        ),
        alert={
            "source": "Datadog",
            "service": "currencyservice",
            "environment": "production",
            "metric": "conversion_zero_amount_rate",
            "value": "34%",
            "threshold": "<0.1%",
            "message": (
                "currencyservice anomaly — 34% of convert() "
                "responses return Money{units: 0, nanos: 0}. "
                "Silent data corruption, no application errors."
            ),
        },
        # pino logger: logger.info('Getting supported currencies...')
        #              logger.info(`conversion request successful`)
        #              logger.error(`conversion request failed: ${err}`)
        # NOTE: NaN propagation does NOT throw, so the app logs
        # "conversion request successful" even for corrupt results.
        # Only the monitoring system detects the $0.00 anomaly.
        logs=[
            "INFO  currencyservice Getting supported currencies...",
            "INFO  currencyservice conversion request successful",
            "INFO  currencyservice conversion request successful",
            "INFO  currencyservice Getting supported currencies...",
            "INFO  currencyservice conversion request successful",
            "WARN  monitoring  currencyservice 34% of convert() "
            "responses return Money{units: 0, nanos: 0} — NaN "
            "coercion from division by undefined when "
            "from.currency_code not in currency_conversion.json",
        ],
    ),
    # ---- Scenario 3: Python — recommendation crash ----
    #
    # Online Boutique source locations:
    #   src/recommendationservice/recommendation_server.py  ~line 70
    #     ListRecommendations() handler
    #     → line 75: filtered_products = list(set(product_ids)
    #                - set(request.product_ids))
    #       Removes products already in the user's cart.
    #     → line 78: num_return = max_responses
    #       BUG: does NOT clamp to len(filtered_products).
    #     → line 79: random.sample(range(num_products), num_return)
    #       Crashes with ValueError when num_products < max_responses
    #       (5), i.e. when the user's cart contains enough products to
    #       leave fewer than 5 remaining.
    #
    # NOTE — fork requirement: the upstream source has a min() guard
    #   (num_return = min(max_responses, num_products)) that prevents
    #   the crash.  The demo fork must change line ~78 to:
    #       num_return = max_responses
    #   so that random.sample(range(0), 5) actually crashes.
    #
    # Logger: logger.info("[Recv ListRecommendations] product_ids=..."
    #   fires AFTER random.sample, so crashing requests produce NO
    #   application log.  The ValueError is caught by the gRPC Python
    #   framework (grpc._server) which logs "Exception calling
    #   application: ..." at ERROR level.  There is NO try/except in
    #   the handler itself.
    "recommendation-bug": DemoScenario(
        id="recommendation-bug",
        title="Recommendation Crash on Full Cart",
        service="recommendationservice",
        severity="P2",
        language="python",
        file_path="src/recommendationservice/recommendation_server.py",
        description=(
            "Recommendation service crashes with ValueError when "
            "a user's cart contains all available products. "
            "random.sample() is called with num_return=5 but "
            "range(0) as the population, because "
            "filtered_products is empty after removing cart items."
        ),
        alert={
            "source": "Prometheus",
            "service": "recommendationservice",
            "environment": "production",
            "metric": "grpc_server_handled_total_UNKNOWN",
            "value": "12%",
            "threshold": "<1%",
            "message": (
                "recommendationservice gRPC UNKNOWN error rate "
                "spike — 12% of ListRecommendations requests "
                "failing. Correlates with large-cart sessions."
            ),
        },
        # Custom JSON logger (via pythonjsonlogger):
        #   logger.info("[Recv ListRecommendations] product_ids=
        #     {}".format(prod_list))
        #   — fires AFTER random.sample, so only successful
        #     requests produce this line.
        # gRPC framework (grpc._server):
        #   "Exception calling application: <exception>"
        #   — logged at ERROR for unhandled handler exceptions.
        logs=[
            "INFO  recommendationservice "
            "[Recv ListRecommendations] product_ids="
            "['OLJCESPC7Z', '1YMWWN1N4O', '2ZYFJ3GM2N']",
            "ERROR recommendationservice "
            "Exception calling application: "
            "ValueError: Sample larger than population "
            "or is negative",
            "INFO  recommendationservice "
            "[Recv ListRecommendations] product_ids="
            "['9SIQT8TOJO', 'L9ECAV7KIM']",
            "ERROR recommendationservice "
            "Exception calling application: "
            "ValueError: Sample larger than population "
            "or is negative",
            "WARN  monitoring  recommendationservice "
            "error_rate=12% — gRPC UNKNOWN errors, all from "
            "carts containing all 9 catalog products "
            "(filtered_products becomes empty)",
        ],
    ),
}
