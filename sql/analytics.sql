CREATE OR REPLACE VIEW position_stats AS
SELECT
    position,
    COUNT(*) AS n,
    ROUND(AVG(team_points), 3) AS avg_points
FROM debate_teams
WHERE position IN ('OG', 'OO', 'CG', 'CO')
GROUP BY position;

CREATE OR REPLACE VIEW bench_stats AS
SELECT
    CASE WHEN position IN ('OG', 'CG') THEN 'Government' ELSE 'Opposition' END AS bench,
    COUNT(*) AS n,
    ROUND(AVG(team_points), 3) AS avg_points
FROM debate_teams
WHERE position IN ('OG', 'OO', 'CG', 'CO')
GROUP BY 1;

CREATE OR REPLACE VIEW half_stats AS
SELECT
    CASE WHEN position IN ('OG', 'OO') THEN 'Opening' ELSE 'Closing' END AS half,
    COUNT(*) AS n,
    ROUND(AVG(team_points), 3) AS avg_points
FROM debate_teams
WHERE position IN ('OG', 'OO', 'CG', 'CO')
GROUP BY 1;

CREATE OR REPLACE VIEW prelim_debate_teams AS
SELECT
    dt.debate_id,
    dt.team_id,
    dt.position,
    dt.team_points,
    r.tournament_id,
    r.seq AS round_seq
FROM debate_teams dt
JOIN debates d ON dt.debate_id = d.debate_id
JOIN rounds r ON d.round_id = r.round_id
WHERE r.stage = 'P'
  AND dt.position IN ('OG', 'OO', 'CG', 'CO');

CREATE OR REPLACE VIEW team_strength AS
SELECT
    *,
    AVG(team_points) OVER (
        PARTITION BY tournament_id, team_id
        ORDER BY round_seq
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ) AS prior_team_strength,
    COUNT(*) OVER (
        PARTITION BY tournament_id, team_id
        ORDER BY round_seq
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ) AS prior_rounds_played
FROM prelim_debate_teams;

CREATE OR REPLACE VIEW team_strength_ranked AS
SELECT
    *,
    RANK() OVER (
        PARTITION BY tournament_id, round_seq
        ORDER BY prior_team_strength DESC NULLS LAST
    ) AS prior_team_rank
FROM team_strength;

CREATE OR REPLACE VIEW final_team_standings AS
SELECT
    tournament_id,
    team_id,
    COUNT(*) AS rounds_played,
    SUM(team_points) AS total_points,
    ROUND(AVG(team_points), 3) AS avg_points,
    RANK() OVER (
        PARTITION BY tournament_id
        ORDER BY SUM(team_points) DESC
    ) AS final_rank
FROM prelim_debate_teams
GROUP BY tournament_id, team_id;

-- One row per prelim debate_team, carrying both the honest prior-only
-- rank and the leaky final rank side by side, for direct comparison.
CREATE OR REPLACE VIEW team_strength_with_final_rank AS
SELECT
    ts.*,
    fs.final_rank,
    fs.total_points AS final_total_points
FROM team_strength_ranked ts
JOIN final_team_standings fs
    ON ts.tournament_id = fs.tournament_id
    AND ts.team_id = fs.team_id;