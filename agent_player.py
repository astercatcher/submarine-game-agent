import json
import os
import random
import socket
import sys

sys.path.append(os.getcwd())

from lib.player_base import Player, PlayerShip


class AgentPlayer(Player):

    def __init__(self):
        initfield = [[i, j] for i in range(Player.FIELD_SIZE)
                      for j in range(Player.FIELD_SIZE)]
        initfield.remove([0,0])
        initfield.remove([0,4])
        initfield.remove([4,0])
        initfield.remove([4,4])
        initfield.remove([2,2])

        # 初期配置
        psw = random.choice(initfield)

        for n in range(-1,2,1):
            for m in range(-1,2,1):
                try:
                    initfield.remove([psw[0]+n,psw[1]+m])
                except ValueError:
                    pass

        psc = random.choice(initfield)
        for n in range(-1,2,1):
            for m in range(-1,2,1):
                try:
                    initfield.remove([psc[0]+n,psc[1]+m])
                except ValueError:
                    pass

        pss = random.choice(initfield)
        positions = {'w': psw, 'c': psc, 's': pss}
        super().__init__(positions)
        self.field = [[0 for i in range(Player.FIELD_SIZE)] for j in range(Player.FIELD_SIZE)]
        self.hitting = None

    # 大体は攻撃する
    # 攻撃したいマスが届かない場合移動する
    def action(self):
        if self.hitting is not None:
            print("hit the same",self.hitting)
            to = self.hitting

            #打てない場合、打ちたいマスの近くに船を動かす
            if not self.can_attack(to):
                moveField = []
                for n in range(-1,2,1):
                    for m in range(-1,2,1):
                        x = to[0]+n
                        y = to[1]+m
                        if x >= 0 and y >= 0 and x<self.FIELD_SIZE and y<self.FIELD_SIZE:
                            moveField.append([to[0]+n,to[1]+m])

                while len(moveField) != 0:
                    to = random.choice(moveField)
                    for shiptype in list(self.ships):
                        if self.ships[shiptype].can_reach(to) and self.overlap(to) is None:
                            print("move to",to,"\n")
                            return json.dumps(self.move(shiptype, to))
                    moveField.remove(to)

                #打ちたいマスの近くに船を動かせない場合
                for i in range(self.FIELD_SIZE):
                    to = [i, self.hitting[1]]
                    for shiptype in list(self.ships):
                        if self.ships[shiptype].can_reach(to) and self.overlap(to) is None:
                            print("move to",to)
                            return json.dumps(self.move(shiptype, to))

            else:
                return json.dumps(self.attack(to))

        else:
            # print(self.field)
            maxNum = max(max(_) for _ in self.field)
            # print("max:",maxNum)
            attackField = []
            moveField = []
            to = []

            for i in range(Player.FIELD_SIZE):
                for j in range(Player.FIELD_SIZE):
                    if self.field[i][j] == maxNum:
                        attackField.append([i,j])

            #attack
            while len(attackField) != 0:
                to = random.choice(attackField)
                if not self.can_attack(to):
                    attackField.remove(to)
                    for n in range(-1,2,1):
                        for m in range(-1,2,1):
                            x = to[0]+n
                            y = to[1]+m
                            if x >= 0 and y >= 0 and x<self.FIELD_SIZE and y<self.FIELD_SIZE:
                                moveField.append([to[0]+n,to[1]+m])
                else:
                    print("attack",to)
                    return json.dumps(self.attack(to))

            #cannot attack block with highest number -> move
            temp = []
            for co in moveField:
                if co not in temp:
                    temp.append(co)
            moveField = temp

            #try to move to feild around the highest number
            while len(moveField) != 0:
                to = random.choice(moveField)
                for shiptype in list(self.ships):
                    if self.ships[shiptype].can_reach(to) and self.overlap(to) is None:
                        print("move to",to)
                        return json.dumps(self.move(shiptype, to))
                moveField.remove(to)


            for i in range(self.FIELD_SIZE):
                goto = [i, to[1]]
                for shiptype in list(self.ships):
                    if self.ships[shiptype].can_reach(goto) and self.overlap(goto) is None:
                        print("move to",goto)
                        return json.dumps(self.move(shiptype, goto))


    def update(self, json_, c):
        super(AgentPlayer,self).update(json_)
        info = json.loads(json_)

        #自分がmoveする時はresultがない
        try:
            resultMes = list(info["result"].keys())[0]
        except KeyError:
            resultMes = None

        if not resultMes is None:
            result = info["result"]

            if resultMes == "attacked":
                pos = result["attacked"]["position"]
                boat = result["attacked"]["near"]
                try:
                    hit = result["attacked"]["hit"]
                except KeyError:
                    hit = None

                # print("position:",pos)
                

                if c == 0: #agent turn
                    if hit is not None: #当たり
                        hit = result["attacked"]["hit"]
                        self.hitting = pos
                        try:
                            hp = info["condition"]["enemy"][hit]["hp"]
                        except KeyError:
                            hp = 0
                        
                        print(hit,"hp:",hp)

                        if hp == 0:
                            self.hitting = None
                            #周り他のshipがない
                            if len(boat) == 0:
                                for n in range(-1,2,1):
                                    for m in range(-1,2,1):
                                        try:
                                            self.field[pos[0]+n][pos[1]+m] = 0
                                        except IndexError:
                                            pass
                            else:
                                for n in range(-1,2,1):
                                    for m in range(-1,2,1):
                                        if not(n == 0 and m == 0):
                                            try:
                                                self.field[pos[0]+n][pos[1]+m] += len(boat)
                                            except IndexError:
                                                pass
                                        else:
                                            self.field[pos[0]][pos[1]] = 0

                   
                    
                    else:
                        self.hitting = None
                        if len(boat) == 0:
                            for i in range(Player.FIELD_SIZE):
                                for j in range(Player.FIELD_SIZE):
                                    #当たってみたマスと周りの8マスをゼロに戻る
                                    if i >= pos[0]-1 and i <= pos[0]+1 and j >= pos[1]-1 and j <= pos[1]+1 and i >= 0 and j >= 0:
                                        self.field[i][j] = 0
                                    else:
                                        self.field[i][j] += 1
                        else:
                            for n in range(-1,2,1):
                                for m in range(-1,2,1):
                                    if not(n == 0 and m == 0):
                                        try:
                                            self.field[pos[0]+n][pos[1]+m] += len(boat)
                                        except IndexError:
                                            pass
                                    else:
                                        self.field[pos[0]][pos[1]] = 0
                

                elif c == 1: #player turn
                    print("attack:",pos)
                    for n in range(-1,2,1):
                        for m in range(-1,2,1):
                            try:
                                self.field[pos[0]+n][pos[1]+m] += 1
                            except IndexError:
                                pass

                print("hit:",hit)
                print("near:",boat,"\n")

            elif resultMes == "moved":
                if c == 1: #player turn
                    temp = [[1 for _ in range(self.FIELD_SIZE)]for _ in range(self.FIELD_SIZE)]
                    dis = result["moved"]['distance']
                    ship = result["moved"]['ship']
                    
                    print(ship, "moved", dis,"\n")

                    if len(info["condition"]["enemy"].keys()) == 1:
                        for i in range(Player.FIELD_SIZE):
                            for j in range(Player.FIELD_SIZE):
                                x = i-dis[0]
                                y = j-dis[1]
                                if x>=0 and y>=0 and x<self.FIELD_SIZE and y<self.FIELD_SIZE:
                                    temp[i][j] = self.field[x][y]
                                else:
                                    temp[i][j] = 0
                        self.field = temp
                    else:
                        if dis[0] != 0:
                            if dis[0] > 0:
                                for i in range(0,dis[0]):
                                        temp[i] = [-1 for _ in range(self.FIELD_SIZE)]
                            else:
                                for i in range(0,dis[0],-1):
                                    temp[4+i] = [-1 for _ in range(self.FIELD_SIZE)]
                        else:
                            if dis[1] > 0:
                                for r in range(self.FIELD_SIZE):
                                    for i in range(0,dis[1]):
                                        temp[r][i] = -1
                            else:
                                for r in range(self.FIELD_SIZE):
                                    for i in range(0,dis[1],-1):
                                        temp[r][4+i] = -1

                        for i in range(self.FIELD_SIZE):
                            for j in range(self.FIELD_SIZE):
                                self.field[i][j] += temp[i][j]
 


# 仕様に従ってサーバとソケット通信を行う．
def main(host, port, seed=0):
    assert isinstance(host, str) and isinstance(port, int)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        with sock.makefile(mode='rw', buffering=1) as sockfile:
            get_msg = sockfile.readline()
            player = AgentPlayer()
            sockfile.write(player.initial_condition()+'\n')
            while True:
                info = sockfile.readline().rstrip()
                print(info)
                if info == "your turn":
                    sockfile.write(player.action()+'\n')
                    get_msg = sockfile.readline()
                    player.update(get_msg,0)
                elif info == "waiting":
                    get_msg = sockfile.readline()
                    player.update(get_msg,1)
                elif info == "you win":
                    break
                elif info == "you lose":
                    break
                elif info == "even":
                    break
                else:
                    raise RuntimeError("unknown information")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Sample Player for Submaline Game")
    parser.add_argument(
        "host",
        metavar="H",
        type=str,
        help="Hostname of the server. E.g., localhost",
    )
    parser.add_argument(
        "port",
        metavar="P",
        type=int,
        help="Port of the server. E.g., 2000",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed of the player",
        required=False,
        default=0,
    )
    args = parser.parse_args()

    main(args.host, args.port, seed=args.seed)
