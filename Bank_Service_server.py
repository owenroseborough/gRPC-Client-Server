# CS4459B Assignment 1 Server Code
# Owen Roseborough
# January 25, 2025

from concurrent import futures
import logging
import grpc
import redis
import json
import time
from redis.lock import Lock
import BankService_pb2
import BankService_pb2_grpc

class BankServiceClass(BankService_pb2_grpc.BankService):

    # Constructor
    def __init__(self):
        retries = 5
        for attempt in range(retries):
            try:
                self.r = redis.Redis()
                self.r.ping()
            except redis.exceptions.ConnectionError as e:
                print(f"Attempt failed: {e}")
                time.sleep(2)

    def CreateAccount(self, request, context):
        # need to create account here in redis, also need to protect with lock
        # because if two clients try to create accounts with the same account_id, would be race condition
        # Create a distributed lock with request.account_id as name
        lock = Lock(self.r, name=request.account_id)
        # Attempt to acquire the lock
        if lock.acquire(sleep=2):
            try:
                # Critical section: Only one client can run this code at a time
                # is account already created?
                if self.r.get(request.account_id) != None:
                    return BankService_pb2.CreateAccountReply(confirmationMessage=f"Account: {request.account_id} already created")
                # else create account
                else:
                    new_account_data = {
                        'account_type': request.account_type,
                        'balance': 0
                    }
                    new_account_data_json = json.dumps(new_account_data)
                    self.r.set(request.account_id, new_account_data_json)
            finally:
                # Always release the lock when done
                lock.release()
        return BankService_pb2.CreateAccountReply(confirmationMessage=f"Account: {request.account_id} of type: {request.account_type} created")
    def GetBalance(self, request, context):
        account_balance = 0
        lock = Lock(self.r, name=request.account_id)
        # Attempt to acquire the lock
        if lock.acquire(sleep=2):
            try:
                # Critical section: Only one client can run this code at a time
                # need to check that account exists
                if self.r.get(request.account_id) == None:
                    # Account not found; set the status code and return an error
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("Account not found. Please check the account ID.")
                    return BankService_pb2.GetBalanceReply()
                # else get account balance
                else:
                    # Retrieve the JSON string from Redis
                    account_data_json = self.r.get(request.account_id)
                    # Deserialize the JSON string back into a Python structure (dictionary)
                    account_data = json.loads(account_data_json)
                    account_balance = account_data["balance"]
            finally:
                # Always release the lock when done
                lock.release()
        return BankService_pb2.GetBalanceReply(balance=account_balance)
    def Deposit(self, request, context):
        # need to check that account exists, amount deposited cannot be negative
        # when depositing need to get lock on account
        lock = Lock(self.r, name=request.account_id)
        # Attempt to acquire the lock
        if lock.acquire(sleep=2):
            try:
                # Critical section: Only one client can run this code at a time
                # need to check that account exists
                if self.r.get(request.account_id) == None:
                    # Account not found; set the status code and return an error
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("Account not found. Please check the account ID.")
                    return BankService_pb2.DepositReply()
                # check that deposit amount is not negative
                elif request.amount <= 0:
                    # Account not found; set the status code and return an error
                    context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                    context.set_details("Transaction amount must be positive.")
                    return BankService_pb2.DepositReply()
                else:
                    # Retrieve the JSON string from Redis
                    account_data_json = self.r.get(request.account_id)
                    # Deserialize the JSON string back into a Python structure (dictionary)
                    account_data = json.loads(account_data_json)
                    account_data["balance"] += request.amount
                    # serialize Python dictionary back into JSON
                    new_account_data_json = json.dumps(account_data)
                    self.r.set(request.account_id, new_account_data_json)
            finally:
                # Always release the lock when done
                lock.release()
        return BankService_pb2.DepositReply(confirmationMessage=f"{request.amount} deposited into: {request.account_id}")
    def Withdraw(self, request, context):
        # need to check that account exists, amount withdrawn must be positive
        # account must have enough funds to service withdrawl
        # when withdrawing need to get lock on account
        lock = Lock(self.r, name=request.account_id)
        # Attempt to acquire the lock
        if lock.acquire(sleep=2):
            try:
                # Critical section: Only one client can run this code at a time
                # need to check that account exists
                if self.r.get(request.account_id) == None:
                    # Account not found; set the status code and return an error
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("Account not found. Please check the account ID.")
                    return BankService_pb2.WithdrawReply()
                # check that withdrawal amount is not negative
                elif request.amount <= 0:
                    context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                    context.set_details("Withdrawal amount must be positive.")
                    return BankService_pb2.WithdrawReply()
                else:
                    # Retrieve the JSON string from Redis
                    account_data_json = self.r.get(request.account_id)
                    # Deserialize the JSON string back into a Python structure (dictionary)
                    account_data = json.loads(account_data_json)
                    if request.amount > account_data["balance"]:
                        context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                        context.set_details("Insufficient funds for the requested withdrawal.")
                        return BankService_pb2.WithdrawReply()
                    account_data["balance"] -= request.amount
                    # serialize Python dictionary back into JSON
                    new_account_data_json = json.dumps(account_data)
                    self.r.set(request.account_id, new_account_data_json)
            finally:
                # Always release the lock when done
                lock.release()
        return BankService_pb2.WithdrawReply(confirmationMessage=f"{request.amount} withdrawn from: {request.account_id}")
    def CalculateInterest(self, request, context):
        # need to check that account exists, interest rate must be positive
        lock = Lock(self.r, name=request.account_id)
        # Attempt to acquire the lock
        if lock.acquire(sleep=2):
            try:
                # Critical section: Only one client can run this code at a time
                # need to check that account exists
                if self.r.get(request.account_id) == None:
                    # Account not found; set the status code and return an error
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("Account not found. Please check the account ID.")
                    return BankService_pb2.CalculateInterestReply()
                # check that withdrawal amount is not negative
                elif request.amount <= 0:
                    context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                    context.set_details("Annual interest rate must be a positive value.")
                    return BankService_pb2.CalculateInterestReply()
                else:
                    # Retrieve the JSON string from Redis
                    account_data_json = self.r.get(request.account_id)
                    # Deserialize the JSON string back into a Python structure (dictionary)
                    account_data = json.loads(account_data_json)
                    account_data["balance"] += account_data["balance"] * (request.annual_interest_rate / 100);
                    # serialize Python dictionary back into JSON
                    new_account_data_json = json.dumps(account_data)
                    self.r.set(request.account_id, new_account_data_json)
            finally:
                # Always release the lock when done
                lock.release()
        return BankService_pb2.CalculateInterestReply(confirmationMessage=f"{request.annual_interest_rate} in interest charged to: {request.account_id}")

def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    BankService_pb2_grpc.add_BankServiceServicer_to_server(BankServiceClass(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig()
    serve()
