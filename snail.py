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
parser.add_argument('-n', type=int, default=1000000, action="store", help="Total sequential search in 1 loop. Default = 1000000")
parser.add_argument('-p', type=str, default='unsolved.txt', action="store", help="Unsolved Puzzles file. Default: unsolved.txt")
parser.add_argument('-ncore', type=int, action="store", help="Number of CPU to use. Default = Total-1")
args = parser.parse_args()
#==============================================================================
seq = args.n
UsedCores = int(args.ncore) if args.ncore else cpu_count() - 1
PuzzFile = args.p if args.p else 'unsolved.txt'  # 'unsolved.txt'
if os.path.isfile(PuzzFile) == False:
    print('File {} not found'.format(PuzzFile))
    sys.exit()
puzz = {int(line.split()[0]):line.split()[1] for line in open(PuzzFile,'r')}
PuzzBits = list(puzz.keys())
PuzzH160 = [bytes.fromhex(ice.address_to_h160(line)) for line in puzz.values()]
#==============================================================================
def randk(bits):
    MIN = 2 ** bits
    MAX = 2 ** (bits + 1)
    return secrets.randbelow(MAX - MIN) + MIN
#==============================================================================
def Generator(counter, match, queue, lock, Loops):
    while not match.is_set():
        Loops += 1
        keyInt = randk(159)
        #print(f'[Loop: {Loops}] Key generated: {hex(keyInt)}')
        
        for bits in PuzzBits:
            StartTimeSLoop = time.time()
            FoundInGroup = 0
            BitKey = int('1' + bin(keyInt)[2:][(1 + 159 - (bits-1)):], 2)
            P = ice.scalar_multiplication(BitKey)
            if ice.pubkey_to_h160(0, True, P) in PuzzH160:
                    match.set()
                    queue.put_nowait((BitKey, h160))
                    FoundInGroup += 1
                    
            CurrentPvk = BitKey + 1
            with lock:
                counter.value += seq
            Pv = ice.point_sequential_increment(seq, P)
            
            for t in range(seq):
                h160 = ice.pubkey_to_h160(0, True, (Pv[t * 65:t * 65 + 65]))
                if h160 in PuzzH160:
                    match.set()
                    queue.put_nowait((CurrentPvk + t, h160))
                    FoundInGroup += 1
                    
            ElapsedSL = time.time() - StartTimeSLoop
            with lock:
                print(f'[Loop: {Loops}] [Puzzle: {bits} bit] [Speed: {seq / ElapsedSL:,.2f} Keys/s] [Total: {counter.value:,}] [Elapsed: {ElapsedSL:,.2f} S]  [{hex(BitKey)}]', end='\r')
                #with open('logs.log', 'a') as f:
                    #f.write(f'[Loop: {Loops}] [Puzzle: {bits} bit] [Speed: {seq / ElapsedSL:,.2f} Keys/s] [Total: {counter.value:,}] [Elapsed: {ElapsedSL:,.2f} S]  [{BitKey}]\n')
#==============================================================================
def Snail():
    with Manager() as manager:
        counter = manager.Value('L', 0)
        match = manager.Event()
        queue = manager.Queue()
        lock = manager.Lock()
        StartTime = time.time()
        Loops = 0 
        with Pool(processes=UsedCores) as pool:
            pool.starmap(Generator, [(counter, match, queue, lock, Loops) for _ in range(UsedCores)])

        TotalGenerated = counter.value
        TotalFound = 0

        while not queue.empty():
            PrivateKey, h160 = queue.get()
            TotalFound += 1
            
            print(f"\n=================================== KEYFOUND ===================================")        
            print(f"Puzzle FOUND PrivateKey INT: {PrivateKey}")
            print(f"Puzzle FOUND PrivateKey HEX: {hex(PrivateKey)}")
            WIF = ice.btc_pvk_to_wif(PrivateKey, False)
            Puzadd = ice.privatekey_to_address(0, True, PrivateKey)
            print(f"Puzzle Address             : {Puzadd}\nH160                       : {h160.hex()}\nPrivate Key WIF            : {WIF}")
            print(f"================================================================================")

            with open('KEYFOUNDKEYFOUND.txt', 'a') as fw:
                fw.write(f"PK INT         : {PrivateKey}\n"
                         f"PK HEX         : {hex(PrivateKey)}\n"
                         f"Puzzle Address : {Puzadd}\n"
                         f"H160           : {h160.hex()}\n"
                         f"WIF            : {WIF}\n"
                         f"====================================================================\n")
                        
        executionTime = time.time() - StartTime
        print(f"Total Generated: {'{:,}'.format(TotalGenerated)}, Total Found: {TotalFound}")
        print(f"Execution Time: {executionTime:.2f} seconds")
#==============================================================================
if __name__ == '__main__':
    StartTime = datetime.datetime.now()
    print(f'[+] Starting Multi CPU Snail .... Please Wait     Version [', parser.version,']')
    print(f'[+] Search Mode: Sequential Random in each Loop.')
    print(f'[+] Increment: {seq:,} Per bit range.')
    print(f'[+] Using CPU Threads: {UsedCores}')
    print(f'[+] Total Unsolved: {len(PuzzBits)} Puzzles in the bit range [{min(PuzzBits)}-{max(PuzzBits)}]')

    try:
        Snail()
    except (KeyboardInterrupt, SystemExit):
        print('\nSIGINT or CTRL-C detected. Exiting gracefully. BYE')
        match.set()  
    finally:
        print(f"Overall Execution Time: {datetime.datetime.now() - StartTime}")
