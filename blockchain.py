#!/usr/bin/python3
import json
import hashlib
from uuid import uuid4
import requests
import os

from flask import Flask, jsonify, request
from time import time, sleep
from urllib.parse import urlparse
from kubernetes import client, config


                

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set() # nodes are the workers

        # initialize the genesis block
        self.new_block(previous_hash='1', proof=100)
        

    # create new block and add it to the chain
    def new_block(self, proof, previous_hash):
        block = {
                'index' : len(self.chain) + 1,
                'timestamp' : time(),
                'transactions' : self.current_transactions,
                'proof' : proof,
                'previous_hash' : previous_hash
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
    Consensus algorithm: Proof of Work (PoW)
    compute a hash with previous block's proof
    hash contains 4 leading 0s
    '''
    def proof_of_work(self, last_proof):
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    # validates if the hash of last_proof and proof contains 4 leading 0s
    @staticmethod
    def valid_proof(last_proof, proof):
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
    def validate_chain(self, chain):
        last_block = chain[1]
        current_idx = 2

        while current_idx < len(chain):
            block = chain[current_idx]
            if block['previous_hash'] != self.hash(last_block):
                return False
            elif not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_idx += 1
        return True

    # register new "machine" in the blockchain
    def register_node(self, address):
        # parsed_url = urlparse(address)
        self.nodes.add(address)
        
    # blockchain conflicts can occur due to several cases, explained here:
    # https://www.geeksforgeeks.org/blockchain-forks/
    # In our case we will update the blockchain with the largest blockchain
    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get(f'http://{node}:5000/chain') 

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

'''
I will use Flask framework to map endpoints to python functions; 
hence allowing us to talk to our blockchain over the web using HHTP requests
I will create four methods:
/transactions : to tell total number of transactions
/transactions/new: to create new transaction to the block
/mine: to tell our worker node to mine a new block
/chain: to return full blockchain
/nodes/register: register worker node in the blockchain
/nodes/resolve: resolve blockchain conflicts and update blockchain
/nodes: total number of worker nodes
'''

# Instantiate node
app = Flask(__name__)

# Generate globally unique address to this node
node_identifier = str(uuid4()).replace('-','')

# Instantiate the blockchain
blockchain = Blockchain()

@app.route('/', methods=['GET'])
def start():
    return "Let's start!", 200

@app.route('/mine', methods=['GET'])
def mine():
    # calculate proof of work == mine a block
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # reward miner by granting him 1 coin
    # the sender is 0 to signify that this node has mined a new coin
    
    blockchain.new_transaction(
        sender = "0",
        recipient = node_identifier,
        amount = 1
    )

    # create new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': 'New Block Added!',
        'index': block['index'],
        'transaction': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }

    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all (k in values for k in required):
        return "Missing values"

    # create a new transaction 
    index = blockchain.new_transaction(
        values['sender'],
        values['recipient'],
        values['amount']
    )

    response = {'message': f'Transaction will be added to the block {index}'}
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    
    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message' : 'New nodes have been added',
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consenses():
    replaced = blockchain.resolve_conflicts()
    
    if replaced:
        response = {
            'message' : 'Our blockchain has been replaced',
            'new_chain' : blockchain.chain
        }
    else:
        response = {
            'message' : 'No change in our blockchain',
            'chain' : blockchain.chain
        }

    return jsonify(response), 200

@app.route('/chain')
def full_chain():
    response = {
        'chain' : blockchain.chain,
        'length' : len(blockchain.chain)
    }

    return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201

def register_blockchains():
    if os.getenv('KUBERNETES_SERVICE_HOST'):
        config.load_incluster_config()
        v1 = client.CoreV1Api()

        sleep(10) # sleep 10 seconds so that containers are all running with assined IPs

        ret = v1.list_namespaced_pod(namespace='default')
        pods_ips = [i.status.pod_ip for i in ret.items] # get pods' ips
        pods_ips.remove(os.getenv('POD_IP')) # remove this pod's ip
        
        for node in pods_ips:
            blockchain.register_node(node)

def checker_thread(b):
    while True:
        b.resolve_conflicts()
        sleep(5)

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p','--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()

    register_blockchains()
    app.run(host='0.0.0.0', port=args.port)