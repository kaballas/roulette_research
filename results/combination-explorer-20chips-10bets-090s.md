# Roulette Combination Explorer results

Fair single-zero European wheel; every portfolio has expected profit -stake/37 (return -1/37 per chip). Worst loss is the most negative net profit over the 37 pockets; tail is expected shortfall of loss at the worst 5% probability mass. Profit is net chips for a single spin.

## 20 chips, ≤10 positions, target ≥70% (26/37), highest winning frequency (then smallest worst loss), stakes: any

Returned 1/10 (stop: twin_limit; realised min bet-set distance None).

| Combination | Positions (chips) | Profitable pockets | Worst loss | 5% tail loss | Stake | Solver |
|---|---|---|---|---|---|---|
| A: existing exact-checked evidence | Split 15/18 ×1; Split 19/22 ×1; Split 25/28 ×1; Corner 13/14/16/17 ×2; Corner 20/21/23/24 ×2; Corner 26/27/29/30 ×2; Corner 31/32/34/35 ×2; Dozen 1-12 ×7; Dozen 13-24 ×1; Dozen 25-36 ×1 | 34/37 | -20 | 18.62 | 20 | recorded |
| B: explorer | Split 16/17 ×1; Split 15/18 ×1; Split 21/24 ×1; Corner 19/20/22/23 ×2; Dozen 1-12 ×7; Dozen 13-24 ×1; Dozen 25-36 ×7 | 34/37 | -20 | 18.62 | 20 | limit |

- **A** net by pocket: 0:-20 1:1 2:1 3:1 4:1 5:1 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:-17 34:1 35:1 36:-17
- **B** net by pocket: 0:-20 1:1 2:1 3:1 4:1 5:1 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:-17 14:-17 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1

## 20 chips, ≤10 positions, target ≥70% (26/37), lowest worst loss, stakes: any

Returned 10/10 (stop: count_reached; realised min bet-set distance 8).

| Combination | Positions (chips) | Profitable pockets | Worst loss | 5% tail loss | Stake | Solver |
|---|---|---|---|---|---|---|
| A: existing exact-checked evidence | Split 7/8 ×1; Split 10/11 ×1; Split 9/12 ×1; Street 4/5/6 ×1; Corner 0/1/2/3 ×2; Six-line 16-21 ×1; Dozen 1-12 ×1; Dozen 13-24 ×5; Dozen 25-36 ×7 | 27/37 | -5 | 5.00 | 20 | recorded |
| B: explorer | Split 4/7 ×1; Corner 5/6/8/9 ×2; Street 16/17/18 ×1; Street 0/1/2 ×1; Street 0/2/3 ×1; Six-line 10-15 ×2; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×1; Column 2-35 (1st/2nd/3rd = starts 1/2/3) ×1; Column 3-36 (1st/2nd/3rd = starts 1/2/3) ×1; High 19-36 ×9 | 26/37 | -5 | 5.00 | 20 | optimal |
| C: explorer | Split 0/1 ×1; Corner 2/3/5/6 ×1; Street 13/14/15 ×1; Dozen 1-12 ×1; Dozen 13-24 ×1; Dozen 25-36 ×1; Low 1-18 ×5; High 19-36 ×9 | 26/37 | -7 | 7.00 | 20 | limit |
| D: explorer | Split 22/25 ×1; Corner 11/12/14/15 ×1; Corner 17/18/20/21 ×1; Corner 26/27/29/30 ×1; Corner 32/33/35/36 ×1; Street 0/2/3 ×1; Six-line 4-9 ×2; Six-line 19-24 ×2; Dozen 25-36 ×4; Low 1-18 ×6 | 26/37 | -8 | 8.00 | 20 | limit |
| E: explorer | Corner 8/9/11/12 ×1; Corner 14/15/17/18 ×1; Corner 29/30/32/33 ×1; Corner 31/32/34/35 ×1; Street 19/20/21 ×1; Street 0/2/3 ×1; Six-line 22-27 ×2; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×4; Column 2-35 (1st/2nd/3rd = starts 1/2/3) ×4; Column 3-36 (1st/2nd/3rd = starts 1/2/3) ×4 | 26/37 | -8 | 8.00 | 20 | limit |
| F: explorer | Split 26/27 ×1; Split 11/14 ×1; Corner 5/6/8/9 ×1; Corner 20/21/23/24 ×1; Street 0/2/3 ×1; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×3; Red ×6; Black ×6 | 26/37 | -8 | 8.00 | 20 | limit |
| G: explorer | Street 0/2/3 ×1; Dozen 1-12 ×1; Dozen 13-24 ×3; Dozen 25-36 ×3; Odd ×6; Even ×6 | 26/37 | -8 | 6.62 | 20 | limit |
| H: explorer | Corner 5/6/8/9 ×1; Corner 14/15/17/18 ×1; Corner 20/21/23/24 ×1; Street 0/1/2 ×1; Six-line 16-21 ×1; Dozen 25-36 ×3; Red ×5; Black ×5; Odd ×1; Even ×1 | 26/37 | -8 | 8.00 | 20 | limit |
| I: explorer | Split 0/1 ×1; Corner 13/14/16/17 ×1; Street 22/23/24 ×1; Six-line 4-9 ×1; Dozen 1-12 ×1; Dozen 25-36 ×3; Red ×6; Black ×6 | 26/37 | -8 | 8.00 | 20 | limit |
| J: explorer | Split 20/23 ×1; Split 0/2 ×1; Corner 2/3/5/6 ×1; Corner 8/9/11/12 ×1; Corner 14/15/17/18 ×1; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×3; Red ×6; Black ×6 | 26/37 | -8 | 8.00 | 20 | limit |
| K: explorer | Split 0/3 ×1; Corner 1/2/4/5 ×1; Corner 7/8/10/11 ×1; Corner 16/17/19/20 ×1; Corner 23/24/26/27 ×1; Street 28/29/30 ×1; Street 31/32/33 ×1; Street 34/35/36 ×1; Odd ×6; Even ×6 | 26/37 | -8 | 8.00 | 20 | limit |

- **A** net by pocket: 0:-2 1:1 2:1 3:1 4:-5 5:-5 6:-5 7:1 8:1 9:1 10:1 11:1 12:1 13:-5 14:-5 15:-5 16:1 17:1 18:1 19:1 20:1 21:1 22:-5 23:-5 24:-5 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **B** net by pocket: 0:4 1:-5 2:7 3:-5 4:1 5:1 6:1 7:1 8:1 9:1 10:-5 11:-5 12:-5 13:-5 14:-5 15:-5 16:-5 17:-5 18:-5 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **C** net by pocket: 0:-2 1:11 2:2 3:2 4:-7 5:2 6:2 7:-7 8:-7 9:-7 10:-7 11:-7 12:-7 13:5 14:5 15:5 16:-7 17:-7 18:-7 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **D** net by pocket: 0:-8 1:-8 2:4 3:4 4:4 5:4 6:4 7:4 8:4 9:4 10:-8 11:1 12:1 13:-8 14:1 15:1 16:-8 17:1 18:1 19:-8 20:1 21:1 22:10 23:-8 24:-8 25:10 26:1 27:1 28:-8 29:1 30:1 31:-8 32:1 33:1 34:-8 35:1 36:1
- **E** net by pocket: 0:-8 1:-8 2:4 3:4 4:-8 5:-8 6:-8 7:-8 8:1 9:1 10:-8 11:1 12:1 13:-8 14:1 15:1 16:-8 17:1 18:1 19:4 20:4 21:4 22:4 23:4 24:4 25:4 26:4 27:4 28:-8 29:1 30:1 31:1 32:10 33:1 34:1 35:1 36:-8
- **F** net by pocket: 0:-8 1:1 2:4 3:4 4:1 5:1 6:1 7:1 8:1 9:1 10:1 11:10 12:-8 13:1 14:10 15:-8 16:1 17:-8 18:-8 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:10 27:10 28:1 29:-8 30:-8 31:1 32:-8 33:-8 34:1 35:-8 36:-8
- **G** net by pocket: 0:-8 1:-5 2:7 3:7 4:-5 5:-5 6:-5 7:-5 8:-5 9:-5 10:-5 11:-5 12:-5 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **H** net by pocket: 0:-8 1:4 2:4 3:-8 4:-8 5:1 6:1 7:-8 8:1 9:1 10:-8 11:-8 12:-8 13:-8 14:1 15:1 16:-2 17:7 18:7 19:-2 20:7 21:7 22:-8 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **I** net by pocket: 0:-2 1:13 2:-5 3:-5 4:1 5:1 6:1 7:1 8:1 9:1 10:-5 11:-5 12:-5 13:1 14:1 15:-8 16:1 17:1 18:-8 19:-8 20:-8 21:-8 22:4 23:4 24:4 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **J** net by pocket: 0:-2 1:1 2:19 3:1 4:1 5:1 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:10 21:-8 22:1 23:10 24:-8 25:1 26:-8 27:-8 28:1 29:-8 30:-8 31:1 32:-8 33:-8 34:1 35:-8 36:-8
- **K** net by pocket: 0:-2 1:1 2:1 3:10 4:1 5:1 6:-8 7:1 8:1 9:-8 10:1 11:1 12:-8 13:-8 14:-8 15:-8 16:1 17:1 18:-8 19:1 20:1 21:-8 22:-8 23:1 24:1 25:-8 26:1 27:1 28:4 29:4 30:4 31:4 32:4 33:4 34:4 35:4 36:4

## 20 chips, ≤10 positions, target ≥70% (26/37), smallest losing tail (5% expected shortfall), stakes: any

Returned 10/10 (stop: count_reached; realised min bet-set distance 5).

| Combination | Positions (chips) | Profitable pockets | Worst loss | 5% tail loss | Stake | Solver |
|---|---|---|---|---|---|---|
| A: existing exact-checked evidence | Split 7/8 ×1; Split 10/11 ×1; Split 9/12 ×1; Street 4/5/6 ×1; Corner 0/1/2/3 ×2; Six-line 16-21 ×1; Dozen 1-12 ×1; Dozen 13-24 ×5; Dozen 25-36 ×7 | 27/37 | -5 | 5.00 | 20 | recorded |
| B: explorer | Split 5/6 ×1; Split 1/4 ×1; Corner 0/1/2/3 ×1; Street 0/2/3 ×1; Six-line 7-12 ×2; Dozen 13-24 ×7; Dozen 25-36 ×7 | 28/37 | -8 | 8.00 | 20 | limit |
| C: explorer | Split 33/36 ×1; Street 0/2/3 ×1; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×7; Column 2-35 (1st/2nd/3rd = starts 1/2/3) ×7; Column 3-36 (1st/2nd/3rd = starts 1/2/3) ×4 | 27/37 | -8 | 8.00 | 20 | limit |
| D: explorer | Split 11/12 ×1; Split 1/4 ×1; Split 7/10 ×1; Corner 5/6/8/9 ×1; Street 0/2/3 ×1; Dozen 1-12 ×1; Dozen 13-24 ×7; Dozen 25-36 ×7 | 30/37 | -8 | 8.00 | 20 | limit |
| E: explorer | Corner 4/5/7/8 ×1; Corner 11/12/14/15 ×1; Street 0/1/2 ×1; Red ×3; Black ×3; Odd ×3; Even ×3; High 19-36 ×5 | 28/37 | -8 | 8.00 | 20 | limit |
| F: explorer | Split 4/5 ×1; Split 10/13 ×1; Split 0/1 ×1; Street 16/17/18 ×1; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×1; Column 2-35 (1st/2nd/3rd = starts 1/2/3) ×1; Column 3-36 (1st/2nd/3rd = starts 1/2/3) ×1; Red ×4; Black ×4; High 19-36 ×5 | 26/37 | -9 | 9.00 | 20 | limit |
| G: explorer | Split 18/21 ×1; Split 22/25 ×1; Street 13/14/15 ×1; Street 34/35/36 ×1; Street 0/1/2 ×1; Street 0/2/3 ×1; Six-line 7-12 ×2; Six-line 28-33 ×2; Odd ×5; Even ×5 | 26/37 | -10 | 10.00 | 20 | limit |
| H: explorer | Street 4/5/6 ×1; Street 0/1/2 ×1; Street 0/2/3 ×1; Dozen 13-24 ×4; Dozen 25-36 ×4; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×3; Column 2-35 (1st/2nd/3rd = starts 1/2/3) ×3; Column 3-36 (1st/2nd/3rd = starts 1/2/3) ×3 | 31/37 | -11 | 11.00 | 20 | limit |
| I: explorer | Split 28/29 ×1; Split 30/33 ×1; Corner 31/32/34/35 ×1; Corner 0/1/2/3 ×1; Street 25/26/27 ×2; Street 34/35/36 ×1; Street 0/1/2 ×1; Six-line 7-12 ×2; Dozen 1-12 ×3; Dozen 13-24 ×7 | 26/37 | -11 | 11.00 | 20 | limit |
| J: explorer | Split 34/35 ×1; Split 26/29 ×1; Split 0/1 ×1; Split 0/2 ×1; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×7; Column 2-35 (1st/2nd/3rd = starts 1/2/3) ×2; Column 3-36 (1st/2nd/3rd = starts 1/2/3) ×7 | 29/37 | -14 | 14.00 | 20 | limit |
| K: explorer | Six-line 1-6 ×1; Six-line 7-12 ×1; Dozen 1-12 ×5; High 19-36 ×13 | 30/37 | -20 | 20.00 | 20 | limit |

- **A** net by pocket: 0:-2 1:1 2:1 3:1 4:-5 5:-5 6:-5 7:1 8:1 9:1 10:1 11:1 12:1 13:-5 14:-5 15:-5 16:1 17:1 18:1 19:1 20:1 21:1 22:-5 23:-5 24:-5 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **B** net by pocket: 0:1 1:7 2:1 3:1 4:-2 5:-2 6:-2 7:-8 8:-8 9:-8 10:-8 11:-8 12:-8 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **C** net by pocket: 0:-8 1:1 2:13 3:4 4:1 5:1 6:-8 7:1 8:1 9:-8 10:1 11:1 12:-8 13:1 14:1 15:-8 16:1 17:1 18:-8 19:1 20:1 21:-8 22:1 23:1 24:-8 25:1 26:1 27:-8 28:1 29:1 30:-8 31:1 32:1 33:10 34:1 35:1 36:10
- **D** net by pocket: 0:-8 1:1 2:-5 3:-5 4:1 5:-8 6:-8 7:1 8:-8 9:-8 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **E** net by pocket: 0:-8 1:4 2:4 3:-8 4:1 5:1 6:-8 7:1 8:1 9:-8 10:-8 11:1 12:1 13:-8 14:1 15:1 16:-8 17:-8 18:-8 19:2 20:2 21:2 22:2 23:2 24:2 25:2 26:2 27:2 28:2 29:2 30:2 31:2 32:2 33:2 34:2 35:2 36:2
- **F** net by pocket: 0:-2 1:9 2:-9 3:-9 4:9 5:9 6:-9 7:-9 8:-9 9:-9 10:9 11:-9 12:-9 13:9 14:-9 15:-9 16:3 17:3 18:3 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **G** net by pocket: 0:4 1:2 2:14 3:2 4:-10 5:-10 6:-10 7:2 8:2 9:2 10:2 11:2 12:2 13:2 14:2 15:2 16:-10 17:-10 18:8 19:-10 20:-10 21:8 22:8 23:-10 24:-10 25:8 26:-10 27:-10 28:2 29:2 30:2 31:2 32:2 33:2 34:2 35:2 36:2
- **H** net by pocket: 0:4 1:1 2:13 3:1 4:1 5:1 6:1 7:-11 8:-11 9:-11 10:-11 11:-11 12:-11 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **I** net by pocket: 0:1 1:10 2:10 3:-2 4:-11 5:-11 6:-11 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:4 26:4 27:4 28:-2 29:-2 30:-2 31:-11 32:-11 33:-2 34:1 35:1 36:-8
- **J** net by pocket: 0:16 1:19 2:4 3:1 4:1 5:-14 6:1 7:1 8:-14 9:1 10:1 11:-14 12:1 13:1 14:-14 15:1 16:1 17:-14 18:1 19:1 20:-14 21:1 22:1 23:-14 24:1 25:1 26:4 27:1 28:1 29:4 30:1 31:1 32:-14 33:1 34:19 35:4 36:1
- **K** net by pocket: 0:-20 1:1 2:1 3:1 4:1 5:1 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:-20 14:-20 15:-20 16:-20 17:-20 18:-20 19:6 20:6 21:6 22:6 23:6 24:6 25:6 26:6 27:6 28:6 29:6 30:6 31:6 32:6 33:6 34:6 35:6 36:6

## 20 chips, ≤10 positions, target ≥80% (30/37), highest winning frequency (then smallest worst loss), stakes: any

Returned 1/10 (stop: twin_limit; realised min bet-set distance None).

| Combination | Positions (chips) | Profitable pockets | Worst loss | 5% tail loss | Stake | Solver |
|---|---|---|---|---|---|---|
| A: existing exact-checked evidence | Split 15/18 ×1; Split 19/22 ×1; Split 25/28 ×1; Corner 13/14/16/17 ×2; Corner 20/21/23/24 ×2; Corner 26/27/29/30 ×2; Corner 31/32/34/35 ×2; Dozen 1-12 ×7; Dozen 13-24 ×1; Dozen 25-36 ×1 | 34/37 | -20 | 18.62 | 20 | recorded |
| B: explorer | Split 13/14 ×1; Split 23/24 ×1; Six-line 16-21 ×3; Dozen 1-12 ×7; Dozen 13-24 ×1; Dozen 25-36 ×7 | 34/37 | -20 | 18.62 | 20 | limit |

- **A** net by pocket: 0:-20 1:1 2:1 3:1 4:1 5:1 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:-17 34:1 35:1 36:-17
- **B** net by pocket: 0:-20 1:1 2:1 3:1 4:1 5:1 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:-17 16:1 17:1 18:1 19:1 20:1 21:1 22:-17 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1

## 20 chips, ≤10 positions, target ≥80% (30/37), lowest worst loss, stakes: any

Returned 6/10 (stop: twin_limit; realised min bet-set distance 7).

| Combination | Positions (chips) | Profitable pockets | Worst loss | 5% tail loss | Stake | Solver |
|---|---|---|---|---|---|---|
| A: existing exact-checked evidence | Street 0/2/3 ×1; Corner 8/9/11/12 ×1; Corner 14/15/17/18 ×1; Corner 20/21/23/24 ×1; Corner 26/27/29/30 ×1; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×3; Red ×6; Black ×6 | 30/37 | -8 | 8.00 | 20 | recorded |
| B: explorer | Corner 4/5/7/8 ×1; Street 0/1/2 ×1; Dozen 13-24 ×3; Dozen 25-36 ×3; Low 1-18 ×6; High 19-36 ×6 | 30/37 | -8 | 8.00 | 20 | optimal |
| C: explorer | Corner 14/15/17/18 ×1; Street 4/5/6 ×1; Street 7/8/9 ×1; Street 0/1/2 ×1; Six-line 13-18 ×2; Dozen 1-12 ×3; High 19-36 ×11 | 30/37 | -11 | 11.00 | 20 | limit |
| D: explorer | Split 7/10 ×1; Street 4/5/6 ×1; Street 0/1/2 ×1; Six-line 13-18 ×2; Dozen 1-12 ×1; Dozen 13-24 ×1; Dozen 25-36 ×1; Red ×3; Black ×3; High 19-36 ×6 | 31/37 | -11 | 11.00 | 20 | limit |
| E: explorer | Corner 7/8/10/11 ×1; Corner 0/1/2/3 ×1; Street 4/5/6 ×1; Street 16/17/18 ×1; Street 19/20/21 ×1; Street 22/23/24 ×1; Six-line 4-9 ×2; Six-line 10-15 ×2; Dozen 13-24 ×3; Dozen 25-36 ×7 | 31/37 | -11 | 11.00 | 20 | limit |
| F: explorer | Street 0/2/3 ×1; Six-line 19-24 ×2; Six-line 28-33 ×2; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×1; Column 2-35 (1st/2nd/3rd = starts 1/2/3) ×1; Column 3-36 (1st/2nd/3rd = starts 1/2/3) ×1; Low 1-18 ×9; High 19-36 ×3 | 30/37 | -11 | 11.00 | 20 | limit |
| G: explorer | Split 12/15 ×1; Split 24/27 ×1; Split 33/36 ×1; Corner 0/1/2/3 ×1; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×7; Column 2-35 (1st/2nd/3rd = starts 1/2/3) ×7; Column 3-36 (1st/2nd/3rd = starts 1/2/3) ×2 | 30/37 | -14 | 14.00 | 20 | limit |

- **A** net by pocket: 0:-8 1:1 2:4 3:4 4:1 5:-8 6:-8 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:-8 33:-8 34:1 35:-8 36:-8
- **B** net by pocket: 0:-8 1:4 2:4 3:-8 4:1 5:1 6:-8 7:1 8:1 9:-8 10:-8 11:-8 12:-8 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **C** net by pocket: 0:-8 1:1 2:1 3:-11 4:1 5:1 6:1 7:1 8:1 9:1 10:-11 11:-11 12:-11 13:-8 14:1 15:1 16:-8 17:1 18:1 19:2 20:2 21:2 22:2 23:2 24:2 25:2 26:2 27:2 28:2 29:2 30:2 31:2 32:2 33:2 34:2 35:2 36:2
- **D** net by pocket: 0:-8 1:1 2:1 3:-11 4:1 5:1 6:1 7:7 8:-11 9:-11 10:7 11:-11 12:-11 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **E** net by pocket: 0:-11 1:-11 2:-11 3:-11 4:4 5:4 6:4 7:1 8:1 9:-8 10:1 11:1 12:-8 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1
- **F** net by pocket: 0:-8 1:1 2:13 3:13 4:1 5:1 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:-11 26:-11 27:-11 28:1 29:1 30:1 31:1 32:1 33:1 34:-11 35:-11 36:-11
- **G** net by pocket: 0:-11 1:10 2:10 3:-5 4:1 5:1 6:-14 7:1 8:1 9:-14 10:1 11:1 12:4 13:1 14:1 15:4 16:1 17:1 18:-14 19:1 20:1 21:-14 22:1 23:1 24:4 25:1 26:1 27:4 28:1 29:1 30:-14 31:1 32:1 33:4 34:1 35:1 36:4

## 20 chips, ≤10 positions, target ≥80% (30/37), smallest losing tail (5% expected shortfall), stakes: any

Returned 0/10 (stop: time_limit; realised min bet-set distance None).

| Combination | Positions (chips) | Profitable pockets | Worst loss | 5% tail loss | Stake | Solver |
|---|---|---|---|---|---|---|
| A: existing exact-checked evidence | Street 0/2/3 ×1; Corner 8/9/11/12 ×1; Corner 14/15/17/18 ×1; Corner 20/21/23/24 ×1; Corner 26/27/29/30 ×1; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×3; Red ×6; Black ×6 | 30/37 | -8 | 8.00 | 20 | recorded |

- **A** net by pocket: 0:-8 1:1 2:4 3:4 4:1 5:-8 6:-8 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:-8 33:-8 34:1 35:-8 36:-8

## 20 chips, ≤10 positions, target ≥90% (34/37), highest winning frequency (then smallest worst loss), stakes: any

Returned 1/10 (stop: twin_limit; realised min bet-set distance None).

| Combination | Positions (chips) | Profitable pockets | Worst loss | 5% tail loss | Stake | Solver |
|---|---|---|---|---|---|---|
| A: existing exact-checked evidence | Split 15/18 ×1; Split 19/22 ×1; Split 25/28 ×1; Corner 13/14/16/17 ×2; Corner 20/21/23/24 ×2; Corner 26/27/29/30 ×2; Corner 31/32/34/35 ×2; Dozen 1-12 ×7; Dozen 13-24 ×1; Dozen 25-36 ×1 | 34/37 | -20 | 18.62 | 20 | recorded |
| B: explorer | Corner 20/21/23/24 ×2; Dozen 25-36 ×6; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×1; Column 2-35 (1st/2nd/3rd = starts 1/2/3) ×1; Column 3-36 (1st/2nd/3rd = starts 1/2/3) ×1; Low 1-18 ×9 | 34/37 | -20 | 18.62 | 20 | optimal |

- **A** net by pocket: 0:-20 1:1 2:1 3:1 4:1 5:1 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:-17 34:1 35:1 36:-17
- **B** net by pocket: 0:-20 1:1 2:1 3:1 4:1 5:1 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:-17 20:1 21:1 22:-17 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1

## 20 chips, ≤10 positions, target ≥90% (34/37), lowest worst loss, stakes: any

Returned 1/10 (stop: twin_limit; realised min bet-set distance None).

| Combination | Positions (chips) | Profitable pockets | Worst loss | 5% tail loss | Stake | Solver |
|---|---|---|---|---|---|---|
| A: existing exact-checked evidence | Split 15/18 ×1; Split 19/22 ×1; Split 25/28 ×1; Corner 13/14/16/17 ×2; Corner 20/21/23/24 ×2; Corner 26/27/29/30 ×2; Corner 31/32/34/35 ×2; Dozen 1-12 ×7; Dozen 13-24 ×1; Dozen 25-36 ×1 | 34/37 | -20 | 18.62 | 20 | recorded |
| B: explorer | Split 7/10 ×1; Split 13/16 ×1; Split 14/17 ×1; Split 15/18 ×1; Corner 2/3/5/6 ×2; Corner 8/9/11/12 ×2; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×1; Column 2-35 (1st/2nd/3rd = starts 1/2/3) ×1; Column 3-36 (1st/2nd/3rd = starts 1/2/3) ×1; High 19-36 ×9 | 34/37 | -20 | 18.62 | 20 | optimal |

- **A** net by pocket: 0:-20 1:1 2:1 3:1 4:1 5:1 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:-17 34:1 35:1 36:-17
- **B** net by pocket: 0:-20 1:-17 2:1 3:1 4:-17 5:1 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1

## 20 chips, ≤10 positions, target ≥90% (34/37), smallest losing tail (5% expected shortfall), stakes: any

Returned 1/10 (stop: twin_limit; realised min bet-set distance None).

| Combination | Positions (chips) | Profitable pockets | Worst loss | 5% tail loss | Stake | Solver |
|---|---|---|---|---|---|---|
| A: existing exact-checked evidence | Split 15/18 ×1; Split 19/22 ×1; Split 25/28 ×1; Corner 13/14/16/17 ×2; Corner 20/21/23/24 ×2; Corner 26/27/29/30 ×2; Corner 31/32/34/35 ×2; Dozen 1-12 ×7; Dozen 13-24 ×1; Dozen 25-36 ×1 | 34/37 | -20 | 18.62 | 20 | recorded |
| B: explorer | Split 1/4 ×1; Split 3/6 ×1; Split 7/10 ×1; Corner 8/9/11/12 ×2; Dozen 13-24 ×6; Dozen 25-36 ×6; Column 1-34 (1st/2nd/3rd = starts 1/2/3) ×1; Column 2-35 (1st/2nd/3rd = starts 1/2/3) ×1; Column 3-36 (1st/2nd/3rd = starts 1/2/3) ×1 | 34/37 | -20 | 18.62 | 20 | optimal |

- **A** net by pocket: 0:-20 1:1 2:1 3:1 4:1 5:1 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:-17 34:1 35:1 36:-17
- **B** net by pocket: 0:-20 1:1 2:-17 3:1 4:1 5:-17 6:1 7:1 8:1 9:1 10:1 11:1 12:1 13:1 14:1 15:1 16:1 17:1 18:1 19:1 20:1 21:1 22:1 23:1 24:1 25:1 26:1 27:1 28:1 29:1 30:1 31:1 32:1 33:1 34:1 35:1 36:1

