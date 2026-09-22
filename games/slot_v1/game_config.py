"""Game-specific configuration file, inherits from src/config/config.py"""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "slot_v1"
        self.provider_number = 0
        self.working_name = "Stake Slot V1 (theme TBD)"
        self.wincap = 5000.0
        self.win_type = "lines"
        self.rtp = 0.9650
        self.construct_paths()

        # Game Dimensions
        self.num_reels = 5
        self.num_rows = [3] * self.num_reels
        # Board and Symbol Properties
        # Paytable designed per CLAUDE.md section 4: H1 5-of-a-kind ~10-25x,
        # L5 3-of-a-kind ~0.1-0.2x, wild pays slightly above H1 (rarer line).
        self.paytable = {
            (5, "W"): 22,
            (4, "W"): 9,
            (3, "W"): 3.5,
            (5, "H1"): 18,
            (4, "H1"): 7,
            (3, "H1"): 2.5,
            (5, "H2"): 12,
            (4, "H2"): 4.5,
            (3, "H2"): 1.5,
            (5, "H3"): 8,
            (4, "H3"): 3,
            (3, "H3"): 1,
            (5, "H4"): 5,
            (4, "H4"): 2,
            (3, "H4"): 0.5,
            (5, "L1"): 3,
            (4, "L1"): 1,
            (3, "L1"): 0.3,
            (5, "L2"): 2.5,
            (4, "L2"): 0.8,
            (3, "L2"): 0.2,
            (5, "L3"): 2,
            (4, "L3"): 0.6,
            (3, "L3"): 0.2,
            (5, "L4"): 1.5,
            (4, "L4"): 0.5,
            (3, "L4"): 0.1,
            (5, "L5"): 1,
            (4, "L5"): 0.3,
            (3, "L5"): 0.1,
        }

        self.paylines = {
            1: [
                0,
                0,
                0,
                0,
                0,
            ],
            2: [
                1,
                1,
                1,
                1,
                1,
            ],
            3: [
                2,
                2,
                2,
                2,
                2,
            ],
            4: [
                0,
                1,
                2,
                1,
                0,
            ],
            5: [
                2,
                1,
                0,
                1,
                2,
            ],
            6: [
                0,
                0,
                1,
                2,
                2,
            ],
            7: [
                2,
                2,
                1,
                0,
                0,
            ],
            8: [
                1,
                0,
                1,
                2,
                1,
            ],
            9: [
                1,
                2,
                1,
                0,
                1,
            ],
            10: [
                0,
                1,
                1,
                1,
                2,
            ],
            11: [
                2,
                1,
                1,
                1,
                0,
            ],
            12: [
                0,
                1,
                0,
                1,
                2,
            ],
            13: [
                2,
                1,
                2,
                1,
                0,
            ],
            14: [
                1,
                1,
                0,
                1,
                1,
            ],
            15: [
                1,
                1,
                2,
                1,
                1,
            ],
            16: [
                0,
                2,
                1,
                0,
                2,
            ],
            17: [
                2,
                0,
                1,
                2,
                0,
            ],
            18: [
                0,
                0,
                2,
                0,
                0,
            ],
            19: [
                2,
                2,
                0,
                2,
                2,
            ],
            20: [
                1,
                0,
                0,
                0,
                1,
            ],
        }

        self.include_padding = True
        self.special_symbols = {"wild": ["W"], "scatter": ["S"], "multiplier": ["W"]}

        # CLAUDE.md section 4: 3/4/5 scatters -> 10/12/15 free spins; retrigger
        # is a flat +5 for 3+ scatters landed during free spins (no scaling
        # with scatter count, unlike the upstream example).
        self.freespin_triggers = {
            self.basegame_type: {3: 10, 4: 12, 5: 15},
            self.freegame_type: {3: 5, 4: 5, 5: 5},
        }
        self.anticipation_triggers = {
            self.basegame_type: min(self.freespin_triggers[self.basegame_type].keys()) - 1,
            self.freegame_type: min(self.freespin_triggers[self.freegame_type].keys()) - 1,
        }
        # Reels
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv", "WCAP": "FRWCAP.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        self.padding_reels[self.basegame_type] = self.reels["BR0"]
        self.padding_reels[self.freegame_type] = self.reels["FR0"]
        # Wild multiplier values restricted to CLAUDE.md's set: x2/x3/x5,
        # x10 rare. Multiple wild-multiplier symbols on one line ADD (see
        # docs/DECISIONS.md), so keeping x10 as the ceiling (vs. the
        # upstream example's x50) is intentional and re-verified against
        # the wincap distribution below (the SDK clamps final_win to the
        # wincap regardless of overshoot, so reaching >=5000x organically
        # via several simultaneous wild-heavy lines is enough - it does not
        # need to land on exactly 5000x).
        self.padding_symbol_values = {"W": {"multiplier": {2: 100, 3: 50, 5: 30, 10: 5}}}

        freegame_condition = {
            "reel_weights": {
                self.basegame_type: {"BR0": 1},
                self.freegame_type: {"FR0": 1},
            },
            "scatter_triggers": {3: 50, 4: 20, 5: 5},
            "mult_values": {
                self.basegame_type: {1: 1},
                self.freegame_type: {2: 60, 3: 30, 5: 8, 10: 2},
            },
            "force_wincap": False,
            "force_freegame": True,
        }

        basegame_condition = {
            "reel_weights": {self.basegame_type: {"BR0": 1}},
            "mult_values": {self.basegame_type: {1: 1}},
            "force_wincap": False,
            "force_freegame": False,
        }

        wincap_condition = {
            "reel_weights": {
                self.basegame_type: {"BR0": 1},
                self.freegame_type: {"FR0": 1, "WCAP": 5},
            },
            "mult_values": {
                self.basegame_type: {1: 1},
                # Dev pass showed the wincap distribution needed 1000+
                # internal retries to organically reach 5000x with a
                # 2/3/5/10-mixed pool; dropping straight to a 5/10-only,
                # 10-heavy pool converges much faster (docs/DECISIONS.md).
                self.freegame_type: {5: 20, 10: 80},
            },
            "scatter_triggers": {4: 1, 5: 2},
            "force_wincap": True,
            "force_freegame": True,
        }

        zerowin_condition = {
            "reel_weights": {self.basegame_type: {"BR0": 1}},
            "mult_values": {
                self.basegame_type: {1: 1},
                self.freegame_type: {2: 100, 3: 60, 5: 20, 10: 3},
            },
            "force_wincap": False,
            "force_freegame": False,
        }

        mode_maxwins = {"base": 5000, "bonus": 5000}
        # Contains all game-logic simulation conditions
        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=mode_maxwins["base"],
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.001,
                        win_criteria=mode_maxwins["base"],
                        conditions=wincap_condition,
                    ),
                    Distribution(criteria="freegame", quota=0.1, conditions=freegame_condition),
                    Distribution(criteria="0", quota=0.4, win_criteria=0.0, conditions=zerowin_condition),
                    Distribution(criteria="basegame", quota=0.5, conditions=basegame_condition),
                ],
            ),
            BetMode(
                name="bonus",
                cost=100.0,
                rtp=self.rtp,
                max_win=mode_maxwins["bonus"],
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.001,
                        win_criteria=mode_maxwins["bonus"],
                        conditions=wincap_condition,
                    ),
                    Distribution(criteria="freegame", quota=0.1, conditions=freegame_condition),
                ],
            ),
        ]
