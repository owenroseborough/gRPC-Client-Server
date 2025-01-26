# CS4459B Assignment 1 Client Code
# Owen Roseborough
# January 25, 2025

from __future__ import print_function
import logging
import grpc
import random
import BankService_pb2
import BankService_pb2_grpc

def create_account(account_id, account_type):
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = BankService_pb2_grpc.BankServiceStub(channel)
        response = stub.CreateAccount(BankService_pb2.CreateAccountRequest(account_id=account_id, account_type=account_type))
        return response.confirmationMessage

def get_balance(account_id):
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = BankService_pb2_grpc.BankServiceStub(channel)
        response = stub.GetBalance(BankService_pb2.BalanceRequest(account_id=account_id))
        return response.balance

def deposit(account_id, amount):
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = BankService_pb2_grpc.BankServiceStub(channel)
        response = stub.Deposit(BankService_pb2.DepositRequest(account_id=account_id, amount=amount))
        return response.confirmationMessage

def withdraw(account_id, amount):
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = BankService_pb2_grpc.BankServiceStub(channel)
        response = stub.Withdraw(BankService_pb2.WithdrawRequest(account_id=account_id, amount=amount))
        return response.confirmationMessage

def calculate_interest(account_id, annual_interest_rate):
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = BankService_pb2_grpc.BankServiceStub(channel)
        response = stub.CalculateInterest(BankService_pb2.CalculateInterestRequest(account_id=account_id, annual_interest_rate=annual_interest_rate))
        return response.confirmationMessage

if __name__ == "__main__":
    logging.basicConfig()
    accountList = []
    accountTypes = ["chequing","savings"]
    
    random.seed(42)
    # create a hundred random accounts
    for account in range(5):
        accountList.append(str(random.randint(1, 100000)))
        create_account(accountList[-1], accountTypes[random.randint(0, 1)])

    # deposit random amounts between $0 and $1000 into every account
    for account in accountList:
        deposit(account, random.random() * 1000)

    # check balances of every account
    for account in accountList:
        get_balance(account)

    # withdraw random amounts between $0 and $1000 from every account
    for account in accountList:
        withdraw(account, random.random() * 1000)

    # check balances of every account
    for account in accountList:
        get_balance(account)

    # calculate random interest amounts between 0% and %100
    for account in accountList:
        calculate_interest(account, random.random())
    
    # check balances of every account
    for account in accountList:
        get_balance(account)
