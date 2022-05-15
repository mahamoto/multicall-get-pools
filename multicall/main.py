from brownie import accounts, network, multicall, Contract, exceptions, web3, chain
import sys, os, csv
import copy
from os.path import dirname, abspath

import dotenv

VERBOSE = True
PATH = dirname(abspath(__file__))
FILEPATH = PATH + "/pooldata/"
BROWNIE_NETWORK = "avax-main"

FLUSH_INTERVALL = 500
# ACCOUNT = ()

dotenv.load_dotenv(PATH + "/.env")
os.environ["SNOWTRACE_TOKEN"] = str(os.getenv("SNOWTRACE_TOKEN"))


EXCHANGES = [
    #{
    #    "name": "SushiSwap",
    #    "filename": "sushi_pools.csv",
    #    "factory_address": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
    #},
    #{
    #    "name": "TraderJoe",
    #    "filename": "traderjoe_pools.csv",
    #    "factory_address": "0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10"
    #},
    {
        "name": "Pangolin",
        "filename": "pangolin_pools.csv",
        "factory_address": "0xefa94DE7a4656D787667C749f7E1223D71E9FD88"    
    }
]

def printv(message: str):
    if VERBOSE:
        print(message)

def main():
    try:
        network.connect("avax-main")
        print(f"Connected to {BROWNIE_NETWORK}")
    except Exception as e:
        sys.exit(f"Error connecting with network {BROWNIE_NETWORK}: {e}")
    
    for name, filename, factory_address in [
        (
            exchange["name"], 
            exchange["filename"], 
            exchange["factory_address"],
        ) for exchange in EXCHANGES]:
        printv(name)

        try:
            factory = Contract.from_explorer(factory_address, silent=True)
        except exceptions.BrownieCompilerWarning as e:
            pass

        pool_amount = int(factory.allPairsLength())
        printv(f"found {pool_amount} pools on {name}")

        # Getting ABI for LP
        try:
            LP_ABI = Contract.from_explorer(
                address = factory.allPairs(0),
                silent=True,
            ).abi
        except exceptions.BrownieCompilerWarning:
            pass

        current_block = chain.height

        pool_addresses = []

        with multicall(
            block_identifier=current_block,
        ):
            for i, pool_id in enumerate(range(pool_amount)):
                if i % FLUSH_INTERVALL == 0 and i !=0:
                    multicall.flush()
                    printv(f"found {i} pool addresses")
                pool_addresses.append(
                    factory.allPairs(pool_id)
                )

        print(f"- Creating LP Objects")

        pools = []

        for i, address in enumerate(pool_addresses):
            if i % FLUSH_INTERVALL == 0 and i != 0:
                multicall.flush()
                printv(f"created {i} pools.")
            pools.append(
                Contract.from_abi(
                    name="",
                    address=address,
                    abi=LP_ABI,
                )
            )
        printv(f"created {len(pools)} objects")

        print(f"- Getting token0 data")

        pool_token0_addresses = []

        with multicall(
            block_identifier=current_block
        ):
            for i, pool_object in enumerate(pools):
                if i % FLUSH_INTERVALL == 0 and i != 0:
                    multicall.flush()
                    printv(f"fetched {i} addresses")
                pool_token0_addresses.append(
                    pool_object.token0()
                )
            print(f"fetched {len(pools)} addresses")

        print(f"- Getting token1 data")

        pool_token1_addresses = []

        with multicall(
            block_identifier=current_block
        ):
            for i, pool_object in enumerate(pools):
                if i % FLUSH_INTERVALL == 0 and i != 0:
                    multicall.flush()
                    printv(f"fetched {i} addresses")
                pool_token1_addresses.append(
                    pool_object.token1()
                )
            print(f"fetched {len(pools)} addresses")
            
        rows = list(
            zip(
                pool_addresses,
                pool_token0_addresses,
                pool_token1_addresses,
            )
        )

        print(f"- Saving pool data in {filename}")

        headers = ["pool", "token0", "token1"]

        with open(FILEPATH + filename, "w") as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(headers)
            csv_writer.writerows(rows)
                

if __name__ == "__main__":
    main()

    


