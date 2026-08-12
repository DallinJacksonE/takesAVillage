CREATE TABLE IF NOT EXISTS `users` (
              `id` INT AUTO_INCREMENT PRIMARY KEY,
              `uuid` VARCHAR(36) NOT NULL UNIQUE,
              `consent_agreed` BOOLEAN NOT NULL,
              `created_at` DATETIME NOT NULL
            );
            CREATE TABLE IF NOT EXISTS `game_history` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `game_id` VARCHAR(64) NOT NULL,
                `day_num` INT NOT NULL,
                `phase` VARCHAR(32) NOT NULL,
                `data` JSON NOT NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX(`game_id`),
                INDEX(`day_num`),
                INDEX(`phase`)
            );
            CREATE TABLE IF NOT EXISTS `player_snapshots` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `game_id` VARCHAR(64) NOT NULL,
                `day_num` INT NOT NULL,
                `phase` VARCHAR(32) NOT NULL,
                `player_id` VARCHAR(64) NOT NULL,
                `name` VARCHAR(32) NOT NULL,
                `health` VARCHAR(16) NOT NULL,
                `sickness_chance` FLOAT NOT NULL,
                `resources` JSON NOT NULL,
                `fire_status` VARCHAR(16) NOT NULL,
                `fire_guests` JSON NOT NULL,
                `developments` JSON NOT NULL,
                `actions` JSON NOT NULL,
                `committed_action` JSON,
                `available_work` JSON NOT NULL,
                `finished_phase` BOOLEAN NOT NULL,
                `timeline` JSON NOT NULL,
                `trade_history` JSON NOT NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX(`game_id`),
                INDEX(`player_id`),
                INDEX(`day_num`),
                INDEX(`phase`)
            );
            CREATE TABLE IF NOT EXISTS `work_phase_snapshots` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `game_id` VARCHAR(64) NOT NULL,
                `player_id` VARCHAR(64) NOT NULL,
                `day_num` INT NOT NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `health` VARCHAR(16) NOT NULL,
                `sickness_chance` FLOAT NOT NULL,
                `wood` INT NOT NULL DEFAULT 0,
                `food` INT NOT NULL DEFAULT 0,
                `iron` INT NOT NULL DEFAULT 0,
                `available_work` JSON NOT NULL,
                `committed_action` JSON,
                INDEX(`game_id`),
                INDEX(`player_id`),
                INDEX(`day_num`)
            );
            CREATE TABLE IF NOT EXISTS `trade_phase_snapshots` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `game_id` VARCHAR(64) NOT NULL,
                `player_id` VARCHAR(64) NOT NULL,
                `day_num` INT NOT NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `health` VARCHAR(16) NOT NULL,
                `sickness_chance` FLOAT NOT NULL,
                `wood` INT NOT NULL DEFAULT 0,
                `food` INT NOT NULL DEFAULT 0,
                `iron` INT NOT NULL DEFAULT 0,
                `trade_history` JSON NOT NULL,
                INDEX(`game_id`),
                INDEX(`player_id`),
                INDEX(`day_num`)
            );
            CREATE TABLE IF NOT EXISTS `night_phase_snapshots` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `game_id` VARCHAR(64) NOT NULL,
                `player_id` VARCHAR(64) NOT NULL,
                `day_num` INT NOT NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `health` VARCHAR(16) NOT NULL,
                `sickness_chance` FLOAT NOT NULL,
                `wood` INT NOT NULL DEFAULT 0,
                `food` INT NOT NULL DEFAULT 0,
                `iron` INT NOT NULL DEFAULT 0,
                `fire_status` VARCHAR(16) NOT NULL,
                `fire_guests` JSON NOT NULL,
                INDEX(`game_id`),
                INDEX(`player_id`),
                INDEX(`day_num`)
            );
            CREATE TABLE IF NOT EXISTS `games` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `game_id` VARCHAR(64) NOT NULL UNIQUE,
                `day_num` INT NOT NULL,
                `phase` VARCHAR(32) NOT NULL,
                `data` JSON NOT NULL,
                `game_type` VARCHAR(32) NOT NULL DEFAULT 'human',
                `training_batch_id` VARCHAR(64),
                `training_generation` INT,
                `trade_count` INT NOT NULL DEFAULT 0,
                `contest_count` INT NOT NULL DEFAULT 0,
                `lie_count` INT NOT NULL DEFAULT 0,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_created_at (created_at),
                INDEX idx_training_batch_id (training_batch_id)
            );
            CREATE TABLE IF NOT EXISTS `training_batches` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `batch_id` VARCHAR(64) NOT NULL UNIQUE,
                `status` VARCHAR(32) NOT NULL,
                `ruleset` VARCHAR(64),
                `bot_model` VARCHAR(64),
                `bot_count` INT,
                `total_generations` INT,
                `current_generation` INT DEFAULT 0,
                `current_game_id` VARCHAR(64),
                `started_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `completed_at` DATETIME,
                `last_heartbeat_at` DATETIME,
                `phase` VARCHAR(64),
                `last_error` TEXT,
                `base_genome_id` VARCHAR(64),
                `final_champion_genome_id` VARCHAR(64),
                `config` JSON,
                `generation_statistics` JSON,
                `games` JSON,
                INDEX idx_training_batches_started_at (started_at)
            );
            CREATE TABLE IF NOT EXISTS `research_visualizations` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `scope_type` VARCHAR(32) NOT NULL,
                `scope_id` VARCHAR(64) NOT NULL,
                `name` VARCHAR(128) NOT NULL,
                `title` VARCHAR(255) NOT NULL,
                `mime_type` VARCHAR(64) NOT NULL,
                `image_bytes` LONGBLOB NOT NULL,
                `metadata` JSON,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_research_visualizations_scope (scope_type, scope_id)
            );
            CREATE TABLE IF NOT EXISTS `genomes` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `shorthand_name` VARCHAR(4) NOT NULL,
                `name` VARCHAR(64) NOT NULL,
                `genome_data` JSON NOT NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
