"""Rule-Based Agents for BANK! dice game.

A collection of agents that use explicit rules and heuristics to make
banking decisions. These agents demonstrate various strategies and serve
as baselines for comparing learning agents.
"""

from __future__ import annotations

from bank.agents.base import Action, Agent, Observation


class ThresholdAgent(Agent):
    """Agent that banks when the bank reaches a fixed threshold.

    Simple strategy: wait until the bank value equals or exceeds a
    predetermined threshold, then bank immediately. This is the most
    straightforward rule-based strategy.

    """

    def __init__(
        self,
        player_id: int,
        threshold: int = 50,
        name: str | None = None,
    ) -> None:
        """Initialize the threshold agent.

        Args:
            player_id: Unique identifier for this player (0-based)
            threshold: Bank value at which to bank (default: 50)
            name: Optional name for display purposes

        """
        super().__init__(player_id, name or f"Threshold-{threshold}")
        self.threshold = threshold

    def act(self, observation: Observation) -> Action:
        """Bank if current bank meets or exceeds threshold.

        Args:
            observation: Current game state information

        Returns:
            "bank" if threshold is met and can_bank is True, otherwise "pass"

        """
        if observation["can_bank"] and observation["current_bank"] >= self.threshold:
            return "bank"
        return "pass"


class ConservativeAgent(Agent):
    """Agent that banks early with low thresholds to avoid risk.

    Conservative strategy: prioritize securing points over maximizing value.
    Banks quickly after the "safe" first three rolls to avoid losing points
    to a seven. Uses lower thresholds and considers roll count.

    """

    def __init__(
        self,
        player_id: int,
        early_threshold: int = 30,
        late_threshold: int = 20,
        name: str | None = None,
    ) -> None:
        """Initialize the conservative agent.

        Args:
            player_id: Unique identifier for this player (0-based)
            early_threshold: Threshold during first 3 rolls (default: 30)
            late_threshold: Threshold after roll 3 (default: 20)
            name: Optional name for display purposes

        """
        super().__init__(player_id, name or "Conservative")
        self.early_threshold = early_threshold
        self.late_threshold = late_threshold

    def act(self, observation: Observation) -> Action:
        """Bank conservatively based on roll count.

        Strategy:
        - First 3 rolls: Bank at early_threshold (less risky period)
        - After roll 3: Bank at late_threshold (more risk of seven)

        Args:
            observation: Current game state information

        Returns:
            "bank" if conditions are met, otherwise "pass"

        """
        if not observation["can_bank"]:
            return "pass"

        # After the safe first 3 rolls, be more conservative
        if observation["roll_count"] > 3:
            threshold = self.late_threshold
        else:
            threshold = self.early_threshold

        if observation["current_bank"] >= threshold:
            return "bank"
        return "pass"


class AggressiveAgent(Agent):
    """Agent that takes risks for higher rewards.

    Aggressive strategy: wait for large bank values before banking.
    Willing to risk losing points to a seven in pursuit of bigger scores.
    Uses higher thresholds and is less affected by roll count.

    """

    def __init__(
        self,
        player_id: int,
        min_threshold: int = 80,
        early_multiplier: float = 1.5,
        name: str | None = None,
    ) -> None:
        """Initialize the aggressive agent.

        Args:
            player_id: Unique identifier for this player (0-based)
            min_threshold: Minimum bank value to consider (default: 80)
            early_multiplier: Multiplier for threshold during first 3 rolls (default: 1.5)
            name: Optional name for display purposes

        """
        super().__init__(player_id, name or "Aggressive")
        self.min_threshold = min_threshold
        self.early_multiplier = early_multiplier

    def act(self, observation: Observation) -> Action:
        """Bank aggressively, waiting for high values.

        Strategy:
        - First 3 rolls: Even higher threshold (safest time to be greedy)
        - After roll 3: Still high threshold but slightly more cautious

        Args:
            observation: Current game state information

        Returns:
            "bank" if high-value conditions are met, otherwise "pass"

        """
        if not observation["can_bank"]:
            return "pass"

        # During first 3 rolls, be even more aggressive (less risk)
        if observation["roll_count"] <= 3:
            threshold = int(self.min_threshold * self.early_multiplier)
        else:
            threshold = self.min_threshold

        if observation["current_bank"] >= threshold:
            return "bank"
        return "pass"


class SmartAgent(Agent):
    """Agent with adaptive strategy based on multiple factors.

    Smart strategy: considers roll count, number of active players,
    recent roll patterns, and competitive position. Adapts behavior
    dynamically based on game context.

    This agent demonstrates how to use all available observation fields
    for decision-making and serves as a template for more sophisticated
    rule-based strategies.

    """

    def __init__(
        self,
        player_id: int,
        base_threshold: int = 50,
        name: str | None = None,
    ) -> None:
        """Initialize the smart agent.

        Args:
            player_id: Unique identifier for this player (0-based)
            base_threshold: Base threshold, adjusted by context (default: 50)
            name: Optional name for display purposes

        """
        super().__init__(player_id, name or "Smart")
        self.base_threshold = base_threshold

    def act(self, observation: Observation) -> Action:
        """Make context-aware banking decisions.

        Strategy considers:
        - Roll count: More conservative after roll 3 (seven risk)
        - Active players: More aggressive if last player
        - Recent roll: React to doubles or near-sevens
        - Bank value: Never bank trivial amounts

        Args:
            observation: Current game state information

        Returns:
            "bank" or "pass" based on multi-factor analysis

        """
        if not observation["can_bank"]:
            return "pass"

        bank = observation["current_bank"]
        roll_count = observation["roll_count"]
        num_active = len(observation["active_player_ids"])
        last_roll = observation["last_roll"]

        # Never bank tiny amounts
        if bank < 15:
            return "pass"

        # Last active player: bank anything reasonable
        if num_active == 1 and bank >= 20:
            return "bank"

        # Calculate dynamic threshold based on context
        threshold = self.base_threshold

        # First 3 rolls: be greedy (sevens add 70, can't lose)
        if roll_count <= 3:
            threshold = int(threshold * 1.5)
        # Rolls 4-6: moderate caution
        elif roll_count <= 6:
            pass  # threshold remains at base value
        # Roll 7+: very risky, be conservative
        else:
            threshold = int(threshold * 0.6)

        # React to recent doubles (bank just doubled or about to)
        if last_roll and roll_count > 3:
            die1, die2 = last_roll
            if die1 == die2 and bank >= threshold * 0.7:
                # Just doubled! Bank immediately if decent value
                return "bank"

        # React to dangerous rolls (near seven)
        if last_roll:
            die1, die2 = last_roll
            roll_sum = die1 + die2
            # If we're seeing 6s or 8s, seven is likely soon
            if roll_sum in (6, 8) and roll_count > 3:
                threshold = int(threshold * 0.8)

        # Standard threshold check
        if bank >= threshold:
            return "bank"

        return "pass"


class AdaptiveAgent(Agent):
    """Agent that adapts strategy based on competitive position.

    Adaptive strategy: adjusts risk tolerance based on relative score.
    When ahead, play conservatively to protect the lead. When behind,
    take more risks to catch up. Demonstrates competitive strategic thinking.

    """

    def __init__(
        self,
        player_id: int,
        default_threshold: int = 50,
        name: str | None = None,
    ) -> None:
        """Initialize the adaptive agent.

        Args:
            player_id: Unique identifier for this player (0-based)
            default_threshold: Threshold when scores are equal (default: 50)
            name: Optional name for display purposes

        """
        super().__init__(player_id, name or "Adaptive")
        self.default_threshold = default_threshold

    def act(self, observation: Observation) -> Action:
        """Adapt strategy based on competitive position.

        Strategy:
        - Leading: Lower threshold (play safe, protect lead)
        - Tied: Default threshold (balanced play)
        - Behind: Higher threshold (take risks to catch up)
        - Far behind: Very high threshold (aggressive catch-up)

        Args:
            observation: Current game state information

        Returns:
            "bank" or "pass" based on competitive position

        """
        if not observation["can_bank"]:
            return "pass"

        my_score = observation["player_score"]
        all_scores = observation["all_player_scores"]
        bank = observation["current_bank"]
        roll_count = observation["roll_count"]

        # Find opponent scores
        opponent_scores = [score for pid, score in all_scores.items() if pid != observation["player_id"]]

        if not opponent_scores:
            # Solo play or testing - use default
            threshold = self.default_threshold
        else:
            leader_score = max(opponent_scores)
            score_diff = my_score - leader_score

            # Adjust threshold based on position
            if score_diff >= 50:
                # Significantly ahead: very conservative
                threshold = int(self.default_threshold * 0.6)
            elif score_diff >= 20:
                # Ahead: conservative
                threshold = int(self.default_threshold * 0.8)
            elif score_diff >= -20:
                # Close: balanced
                threshold = self.default_threshold
            elif score_diff >= -50:
                # Behind: aggressive
                threshold = int(self.default_threshold * 1.3)
            else:
                # Far behind: very aggressive
                threshold = int(self.default_threshold * 1.6)

        # Still consider roll risk
        if roll_count > 6:
            # High risk - reduce threshold regardless of position
            threshold = int(threshold * 0.8)

        if bank >= threshold:
            return "bank"
        return "pass"
