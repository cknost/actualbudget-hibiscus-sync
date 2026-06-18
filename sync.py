import requests
import json
from config import config
import decimal
from datetime import datetime
from actual import Actual
from actual.queries import create_transaction, get_account, match_transaction

def get_transactions():
    transactionssession = requests.Session()
    transactionssession.verify = False
    transactionssession.auth = config.auth
    transactions = transactionssession.get(config.url)
    return transactions.json()

def main():
    transactions = get_transactions()
    with Actual(**config.actual_auth) as actual:
        act = get_account(actual.session, config.bankname)
        trans_number = 0
        for transaction in transactions:
            trans_number += 1
            if "*" in transaction.get("zweck") and not transaction.get("empfaenger_name") :
                transaction["empfaenger_name"] = transaction.get("zweck").split("*")[0]
            if "Kartenzahlung" in transaction.get("zweck") and not transaction.get("empfaenger_name") :
                transaction["empfaenger_name"] = transaction.get("zweck").split(",")[0]
            date = datetime.strptime(transaction["datum"],"%Y-%m-%d")
            if not match_transaction(actual.session, date, act, imported_id=transaction.get("empfaenger_name", "")) and not transaction.get("flags") == "2":
                trans_number += 1
                t = create_transaction(
                    actual.session,
                    date,
                    act,
                    imported_payee = transaction.get("empfaenger_name", ""),
                    notes = transaction.get("zweck",""),
                    amount=decimal.Decimal(transaction.get("betrag")),
                    imported_id=transaction.get("customerref")
                )
            if trans_number == 100:
                actual.commit()
                trans_number = 0
        actual.commit()

if __name__ == '__main__':
    main()
