# -*- coding: utf-8 -*-
"""
Usage :
 > python3 snail.py -n "Total sequential" -p "File Name" -ncore "Number of CPU To Use"
 > python3 snail.py -n 8000000 -p Puzzles67-70.txt -ncore 8 
 
@author: iceland
"""
import argparse
import secp256k1 as ice
import sys, os, time, datetime, secrets
from multiprocessing import Event, Pool, Value, cpu_count, Manager
#==============================================================================
parser = argparse.ArgumentParser(description='This tool use random number reusability for sequentially searching all unsolved BTC puzzles', 
                                 epilog='Enjoy the program! :)    Tips BTC: bc1q39meky2mn5qjq704zz0nnkl0v7kj4uz6r529at')
parser.version = '02052024'  
parser.add_argument('-n', type=int, default=1000000, action="store", help="Total sequential search in 1 loop. default=1000000")
parser.add_argument('-p', type=str, default='unsolved.txt', action="store", help="Unsolved Puzzles file. default=unsolved.txt")
parser.add_argument('-ncore', type=int, action="store", help="Number of CPU to use. default = Total-1")
args = parser.parse_args()
#==============================================================================
seq = args.n
UsedCores = int(args.ncore) if args.ncore else cpu_count() -1
p_file = args.p if args.p else 'unsolved.txt'  # 'unsolved.txt'
if os.path.isfile(p_file) == False:
    print('File {} not found'.format(p_file))
    sys.exit()
puzz = {int(line.split()[0]):line.split()[1] for line in open(p_file,'r')}
PuzzBits = list(puzz.keys())
puzz_h160 = [bytes.fromhex(ice.address_to_h160(line)) for line in puzz.values()]
#==============================================================================
def Generator(counter, match, queue, lock, Loops):
    while not match.is_set():
        Loops += 1
        for bits in PuzzBits:
            MIN = 2 ** (bits - 1)
            MAX = 2 ** bits
            keyInt = secrets.randbelow(MAX - MIN) + MIN
            P = ice.scalar_multiplication(keyInt)
            currentPvk = keyInt + 1
            with lock:
                counter.value += seq
            Pv = ice.point_sequential_increment(seq, P)
            foundInGroup = 0
            startTimeSLoop = time.time()

            for t in range(seq):
                h160 = ice.pubkey_to_h160(0, True, (Pv[t * 65:t * 65 + 65]))
                if h160 in puzz_h160:
                    match.set()
                    queue.put_nowait((currentPvk + t, h160))
                    foundInGroup += 1
                    
            ElapsedSL = time.time() - startTimeSLoop
            with lock:
                print(f'[Loop: {Loops}] [Puzzle: {bits} bit] [Speed: {seq / ElapsedSL:.2f} K/s] [Total: {'{:,}'.format(counter.value)}] [{ElapsedSL:,.2f} S ] [{hex(keyInt)}]', end='\r')
#==============================================================================
def Snail():
    with Manager() as manager:
        counter = manager.Value('L', 0)
        match = manager.Event()
        queue = manager.Queue()
        lock = manager.Lock()
        startTime = time.time()
        Loops = 0 
        with Pool(processes=UsedCores) as pool:
            pool.starmap(Generator, [(counter, match, queue, lock, Loops) for _ in range(UsedCores)])

        totalGenerated = counter.value
        totalFound = 0

        while not queue.empty():
            privateKey, h160 = queue.get()
            totalFound += 1
            
            print(f"\n============== KEYFOUND ==============")        
            print(f"Puzzle FOUND PrivateKey: {hex(privateKey)}")
            wifKey = ice.btc_pvk_to_wif(privateKey, False)
            puzadd = ice.privatekey_to_address(0, True, privateKey)
            print(f"Private Key(wif): {wifKey}\nPuzzle Address: {puzadd}\nH160: {h160.hex()}")
            print(f"======================================")

            with open('KEYFOUNDKEYFOUND.txt', 'a') as fw:
                fw.write(f"H160           :{h160.hex()}\n"
                        f"Puzzle Address :{puzadd}\n"
                        f"WIF            :{wifKey}\n"
                        f"PK             :{privateKey}\n"
                        f"PK HEX         :{hex(privateKey)}\n"
                        f"====================================================================\n")

        executionTime = time.time() - startTime
        print(f"Total Generated: {'{:,}'.format(totalGenerated)}, Total Found: {totalFound}")
        print(f"Execution Time: {executionTime:.2f} seconds")
        
#==============================================================================
if __name__ == '__main__':
    startTime = datetime.datetime.now()
    print('\n[+] Starting Program.... Please Wait !')
    print(f'[+] Search Mode: Sequential Random in each Loop. seq={seq}')
    print(f'[+] Total Unsolved: {len(PuzzBits)} Puzzles in the bit range [{min(PuzzBits)}-{max(PuzzBits)}]')

    try:
        Snail()
    except (KeyboardInterrupt, SystemExit):
        print('\nSIGINT or CTRL-C detected. Exiting gracefully. BYE')
        match.set()  
        
    finally:
        print(f"Overall Execution Time: {datetime.datetime.now() - startTime}")
