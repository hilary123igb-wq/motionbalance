DROP TABLE IF EXISTS debate_teams CASCADE;
DROP TABLE IF EXISTS debates CASCADE;
DROP TABLE IF EXISTS motions CASCADE;
DROP TABLE IF EXISTS rounds CASCADE;
DROP TABLE IF EXISTS team_members CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS participants CASCADE;
DROP TABLE IF EXISTS tournaments CASCADE;

CREATE TABLE tournaments (
    tournament_id   VARCHAR PRIMARY KEY,   -- "{host}:{raw_id}"
    host            VARCHAR,               -- which Tabbycat installation
    slug            VARCHAR,
    name            VARCHAR,
    short_name      VARCHAR,
    source_url      VARCHAR
);

CREATE TABLE participants (
    participant_id  VARCHAR PRIMARY KEY,
    name            VARCHAR,
    anonymous       BOOLEAN
);

CREATE TABLE teams (
    team_id         VARCHAR PRIMARY KEY,
    tournament_id   VARCHAR REFERENCES tournaments(tournament_id),
    team_name       VARCHAR
);

CREATE TABLE team_members (
    team_id         VARCHAR REFERENCES teams(team_id),
    participant_id  VARCHAR REFERENCES participants(participant_id),
    PRIMARY KEY (team_id, participant_id)
);

CREATE TABLE rounds (
    round_id        VARCHAR PRIMARY KEY,
    tournament_id   VARCHAR REFERENCES tournaments(tournament_id),
    seq             INTEGER,
    name            VARCHAR,
    stage           VARCHAR,
    break_category  VARCHAR
);

CREATE TABLE motions (
    motion_id       VARCHAR PRIMARY KEY,
    text            VARCHAR,
    reference       VARCHAR,
    info_slide      VARCHAR
);

CREATE TABLE debates (
    debate_id       VARCHAR PRIMARY KEY,
    round_id        VARCHAR REFERENCES rounds(round_id),
    motion_id       VARCHAR REFERENCES motions(motion_id),
    venue_id        VARCHAR
);

CREATE TABLE debate_teams (
    debate_id       VARCHAR REFERENCES debates(debate_id),
    team_id         VARCHAR REFERENCES teams(team_id),
    position        VARCHAR,
    team_points     INTEGER,
    rank            INTEGER,
    team_score      DOUBLE,
    PRIMARY KEY (debate_id, team_id)
);