#!/usr/bin/python3
import json
import hashlib
import requests

from time import time
from urllib.parse import urlparse


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set() # nodes are the machines!

        # initialize the genesis block
        self.new_block(previous_hash='1', proof=100)

    # create new block and add it to the chain
    def new_block(self, proof, previous_hash):
        block = {
                'index' : len(self.chain) + 1,
                'timestamp' : time(),
                'transactions' : self.current_transactions,
                'proof' : proof,
                'previous_hash' : previous_hash or self.hash(self.chain[-1])
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    # create new transaction and add it to list of transactions for a block
    # return the block index to the which the transaction was added to
    def new_transaction(self, sender, recipient, amount):
        transaction = {
                'sender' : sender,
                'recipient' : recipient,
                'amount' : amount
        }
        self.current_transactions.append(transaction)
        return self.last_block['index'] + 1
    
    @property
    def last_block(self):
        return self.chain[-1]

    '''
    PoW algorithm:
    compute a hash with previous block's proof
    hash contains 4 leading 0s
    '''
    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    # validates if the hash of last_proof and proof contains 4 leading 0s
    @staticmethod
    def valid_proof(self, last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

    # hashes a block
    @staticmethod
    def hash(block):
        block_bytes = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_bytes).hexdigest()

    # validate a blockchain
    # loops through every block and verifies hash and proof
    def validate_chain(self):
        last_block = self.chain[0]
        current_idx = 1

        while current_idx < len(self.chain):
            block = self.chain[current_idx]

            if block['previous_hash'] != self.hash(last_block):
                return False
            elif not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_idx += 1
        return True

    # register new "machine" in the blockchain
    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.validate_chain(chain):
                    max_length = length
                    new_chain = chain
        
        if new_chain:
            self.chain = new_chain
            return True
        
        return False

