from typing import List, Optional, Union
from re import sub, split
import random
import threading
import time

POPULATION = 200


class Individual:
    gnome = [""] * 10

    def __init__(self, gnome: List[str]):
        self.gnome = [*gnome]

    def __str__(self):
        return "".join(self.gnome)

    @property
    def gnome_in_dict(self) -> dict:
        gid = {key: str(value) for value, key in enumerate(self.gnome) if key}
        return gid

    def swap(self, a: int, b: int):
        temp_gnome = [*self.gnome]
        temp_gnome[a], temp_gnome[b] = temp_gnome[b], temp_gnome[a]
        return Individual(temp_gnome)

    def valid(self, operands: List[str], max_len_operand: int) -> bool:
        gid = self.gnome_in_dict
        max_len = 0
        operands = operands[:]
        a = 0
        pivot = None

        for i, operand in enumerate(operands):
            if operand == "=":
                a = i
            new_operand = operand.translate(
                operand.maketrans("".join(gid.keys()), "".join(gid.values()))
            )
            if new_operand[0] == "0" and len(new_operand) > 1:
                return False
            if operand[-1].isalpha() or operand[-1].isdigit():
                new_pivot = 0
                for c in new_operand[::-1]:
                    if c.isdigit():
                        new_pivot -= 1
                    else:
                        break
                if pivot == None:
                    pivot = new_pivot
                elif new_pivot > pivot:
                    pivot = new_pivot
            operands[i] = new_operand

        if pivot >= 0:
            return True

        lhs = "".join([operand[pivot:] for operand in operands[:a]])
        rhs = "".join([operand[pivot:] for operand in operands[a + 1 :]])

        try:
            lhs = str(eval(sub(r"(^|[^0-9])0+([1-9]+)", r"\1\2", lhs)))
            rhs = str(eval(sub(r"(^|[^0-9])0+([1-9]+)", r"\1\2", rhs)))
            return lhs.zfill(-pivot)[pivot:] == rhs.zfill(-pivot)[pivot:]
        except:
            return False

        return True

    def fitness(self, operands: List[str]) -> int:
        gid = self.gnome_in_dict
        operands_str = ""
        for operand in operands:
            new_operand = operand.translate(
                operand.maketrans("".join(gid.keys()), "".join(gid.values()))
            )
            if new_operand[0] == "0" and len(new_operand) > 1:
                return -1
            operands_str += new_operand

        try:
            lhs, rhs = operands_str.split("=")
            lhs = eval(sub(r"(^|[^0-9])0+([1-9]+)", r"\1\2", lhs))
            rhs = eval(sub(r"(^|[^0-9])0+([1-9]+)", r"\1\2", rhs))
            return abs(rhs - lhs)
        except:
            return -1


def generate_next_gen(
    ind: Individual, operands: List[str], iter: int = 1
) -> List[List[Union[int, Individual]]]:
    result = []
    cur_ind = ind
    while len(result) < iter:
        a = random.randint(0, 9)
        b = random.randint(0, 9)
        if a != b:
            new_ind = cur_ind.swap(a, b)
            fitness = new_ind.fitness(operands)
            if fitness == -1:
                continue
            result.append([fitness, new_ind])

    return result


def validate_string(txt: str) -> str:
    txt = txt.replace(" ", "")
    txt = txt.replace("+", " + ")
    txt = txt.replace("-", " - ")
    txt = txt.replace("*", " * ")
    txt = txt.replace("(", " ( ")
    txt = txt.replace(")", " ) ")
    txt = txt.replace("=", " = ")
    return txt


def cryptarithmetic_solve(operands_and_digits: str) -> Optional[Individual]:
    operands_and_digits = validate_string(operands_and_digits)
    THREAD_STATE = {"DONE": False, "RESULT": None}
    OPERANDS = [c for c in split(r" ", operands_and_digits) if c]
    MAX_LEN_OPERAND = max(map(lambda x: len(x), OPERANDS))
    VARIABLES = []

    for i in range(-1, -(MAX_LEN_OPERAND + 1), -1):
        for operand in OPERANDS:
            if i < -len(operand):
                continue
            if operand[i].isalpha() and operand[i] not in VARIABLES:
                VARIABLES.append(operand[i])

    if len(VARIABLES) > 10:
        raise ValueError

    # detect infinity of genetic
    def BACKTRACKING(init_ind: List[str]) -> bool:
        if THREAD_STATE["DONE"]:
            return True
        try:
            # get a char
            word = next(c for c in VARIABLES if c not in init_ind)
        except StopIteration:
            # if all char are in Individual
            ind = Individual(init_ind)
            # calc fitness
            fitness = ind.fitness(OPERANDS)
            if fitness == 0:
                # if fitness == 0 --> GOAL
                THREAD_STATE["DONE"] = True
                THREAD_STATE["RESULT"] = ind
                return True
            return False
        else:
            # get the empty cell
            for i in (index for index, value in enumerate(init_ind) if not value):
                # assgin chosen word into empty cell
                init_ind[i] = word
                # check
                if (
                    len([c for c in init_ind if c]) == len(VARIABLES)
                    or Individual(init_ind).valid(OPERANDS, MAX_LEN_OPERAND)
                ) and BACKTRACKING(init_ind):
                    return True
                init_ind[i] = ""

            # if backtracking run all case but it can not find solutions --> No solution
            empty = True
            for v in init_ind:
                empty = empty and not v
            if empty and not THREAD_STATE["DONE"]:
                THREAD_STATE["DONE"] = True

            return False

    def GENETIC():
        cur_generation = []
        while len(cur_generation) < POPULATION:
            init_ind = ["" for _ in range(10)]  # initial individual
            for c in VARIABLES:
                pos = random.choice(
                    [i for i, v in enumerate(init_ind) if not v]
                )  # choose a empty cell in init_ind
                init_ind[pos] = c
            init_ind = Individual(init_ind)  # init Individual
            fitness = init_ind.fitness(OPERANDS)
            if fitness == -1:
                continue
            cur_generation.append(
                [fitness, init_ind]
            )  # push fitness and individual into current generation

        while not THREAD_STATE["DONE"]:
            cur_generation.sort(key=lambda x: x[0])  # sort generation

            if not cur_generation[0][0]:
                THREAD_STATE["DONE"] = True
                THREAD_STATE["RESULT"] = cur_generation[0][1]
                break

            cur_generation = cur_generation[: int(POPULATION / 10)] + [
                generate_next_gen(
                    random.choice(cur_generation[: int(POPULATION / 2)])[1], OPERANDS, 1
                )[0]
                for _ in range(int(POPULATION * 9 / 10))
            ]

    th = threading.Thread(target=GENETIC)
    th.start()
    BACKTRACKING(["" for _ in range(10)])
    th.join()
    return THREAD_STATE["RESULT"]


if __name__ == "__main__":
    OPERANDS_AND_DIGITS = ""
    with open("input.txt", "r") as file:
        OPERANDS_AND_DIGITS = file.readline().strip()
    print("-----------")
    start_time = time.time()
    result = cryptarithmetic_solve(OPERANDS_AND_DIGITS)
    if result != None:
        gid = result.gnome_in_dict
        result_str = ""
        for c in sorted(gid.keys()):
            result_str += gid[c]
        print("".join(sorted(gid.keys())), "=", result_str)
        with open("output.txt", "w") as file:
            file.write(result_str)
    else:
        print("NO SOLUTION")
        with open("output.txt", "w") as file:
            file.write("NO SOLUTION")
    end_time = time.time()
    print("   total run-time: %f ms" % ((end_time - start_time) * 1000))
    print("-----------")