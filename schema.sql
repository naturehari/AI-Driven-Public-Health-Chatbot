-- ============================================================
--  AI-Driven Public Health Chatbot - MySQL Schema
--  schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS healthbot_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE healthbot_db;

-- ─────────────────────────────────────────
--  Table: users
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id                  INT             UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(120)    NOT NULL,
    email               VARCHAR(180)    NOT NULL UNIQUE,
    password_hash       VARCHAR(256)    NOT NULL,
    preferred_language  VARCHAR(10)     NOT NULL DEFAULT 'en',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────
--  Table: chat_history
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_history (
    id          INT             UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id     INT             UNSIGNED NOT NULL,
    message     TEXT            NOT NULL,
    response    TEXT            NOT NULL,
    language    VARCHAR(10)     NOT NULL DEFAULT 'en',
    timestamp   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chat_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_user_ts (user_id, timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────
--  Table: diseases
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS diseases (
    id          INT             UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(150)    NOT NULL UNIQUE,
    symptoms    TEXT            NOT NULL,
    prevention  TEXT            NOT NULL,
    info_link   VARCHAR(500)    DEFAULT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────
--  Table: vaccines
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vaccines (
    id              INT             UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    disease_id      INT             UNSIGNED NOT NULL,
    vaccine_name    VARCHAR(200)    NOT NULL,
    recommended_age VARCHAR(80)     NOT NULL,
    description     TEXT            NOT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_vaccine_disease
        FOREIGN KEY (disease_id) REFERENCES diseases(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────
--  Table: health_alerts
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS health_alerts (
    id          INT             UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(250)    NOT NULL,
    description TEXT            NOT NULL,
    date_issued DATE            NOT NULL,
    severity    ENUM('low','medium','high','critical') NOT NULL DEFAULT 'medium',
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (date_issued),
    INDEX idx_severity (severity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
--  SEED DATA — Diseases
-- ============================================================
INSERT INTO diseases (name, symptoms, prevention, info_link) VALUES
(
  'Dengue Fever',
  'High fever (40°C/104°F), severe headache, pain behind the eyes, muscle and joint pains, nausea, vomiting, skin rash, mild bleeding (nose or gums).',
  'Eliminate standing water around your home. Use mosquito repellent and wear long-sleeved clothing. Install/repair window and door screens. Use bed nets.',
  'https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue'
),
(
  'Malaria',
  'Fever and chills, headache, nausea and vomiting, muscle pain, fatigue, sweating, chest or abdominal pain. Symptoms appear 10–15 days after bite.',
  'Sleep under insecticide-treated bed nets. Use indoor residual spraying. Take antimalarial prophylaxis when traveling. Drain stagnant water.',
  'https://www.who.int/news-room/fact-sheets/detail/malaria'
),
(
  'COVID-19',
  'Fever, cough, shortness of breath, fatigue, loss of taste or smell, sore throat, headache, body aches, diarrhea. Range from mild to severe.',
  'Get vaccinated and stay up to date on boosters. Wear a well-fitted mask in crowded spaces. Wash hands frequently. Maintain physical distancing.',
  'https://www.who.int/health-topics/coronavirus'
),
(
  'Typhoid',
  'Prolonged high fever, weakness, stomach pain, headache, constipation or diarrhea, loss of appetite, pink spots on trunk. Can become life-threatening.',
  'Drink only treated or boiled water. Eat properly cooked food. Practice good hand hygiene. Get vaccinated before traveling to endemic regions.',
  'https://www.who.int/news-room/fact-sheets/detail/typhoid'
),
(
  'Influenza (Flu)',
  'Sudden onset of fever, cough (usually dry), headache, muscle/joint pain, malaise, sore throat, runny nose. Lasts approximately 5–7 days.',
  'Annual flu vaccination is the most effective prevention. Wash hands regularly. Avoid close contact with sick individuals. Cover coughs and sneezes.',
  'https://www.who.int/news-room/fact-sheets/detail/influenza-(seasonal)'
),
(
  'Cholera',
  'Profuse watery diarrhea (rice-water stool), vomiting, rapid dehydration, muscle cramps, nausea. Severe cases can lead to death within hours.',
  'Drink safe water (boiled or treated). Practice proper sanitation and hygiene. Wash hands with soap. Eat food that is thoroughly cooked.',
  'https://www.who.int/news-room/fact-sheets/detail/cholera'
);


-- ============================================================
--  SEED DATA — Vaccines
-- ============================================================
INSERT INTO vaccines (disease_id, vaccine_name, recommended_age, description) VALUES
-- Dengue (id=1)
(1, 'Dengvaxia (CYD-TDV)', '9–45 years (seropositive only)',
 'A live recombinant tetravalent dengue vaccine. Recommended only for individuals with prior dengue infection confirmed by antibody test.'),
-- Malaria (id=2)
(2, 'RTS,S/AS01 (Mosquirix)', 'Infants 5–17 months',
 'First malaria vaccine approved by WHO. Provides partial protection against Plasmodium falciparum. Administered in 4 doses.'),
-- COVID-19 (id=3)
(3, 'Covishield / AstraZeneca', '18+ years',
 'Viral vector vaccine using a modified chimpanzee adenovirus. Two doses 4–12 weeks apart. Highly effective against severe disease.'),
(3, 'Covaxin (BBV152)', '18+ years',
 'Whole-virion inactivated SARS-CoV-2 vaccine developed in India. Two doses 28 days apart. Approved for emergency use by WHO.'),
-- Typhoid (id=4)
(4, 'Typhoid Conjugate Vaccine (TCV)', '6 months and above',
 'Single-dose injectable conjugate vaccine providing longer-lasting immunity. WHO recommends for children in endemic areas.'),
-- Influenza (id=5)
(5, 'Seasonal Influenza Vaccine', '6 months and above (annually)',
 'Annual vaccination is required as influenza strains change yearly. Available as inactivated (injection) or live attenuated (nasal spray) forms.'),
-- Cholera (id=6)
(6, 'Shanchol / Dukoral', '1 year and above',
 'Oral cholera vaccines providing 65–85% protection. Used in outbreak response and for travelers to endemic regions. Two doses 14 days apart.');


-- ============================================================
--  SEED DATA — Health Alerts
-- ============================================================
INSERT INTO health_alerts (title, description, date_issued, severity) VALUES
('Dengue Outbreak Warning — Tamil Nadu',
 'A significant rise in dengue cases has been reported across Chennai and surrounding districts. Residents are advised to eliminate stagnant water and use mosquito repellents.',
 CURDATE(), 'high'),
('Monsoon Fever Advisory',
 'With the onset of monsoon season, the risk of waterborne diseases including typhoid and cholera increases. Ensure drinking water is treated or boiled.',
 DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'medium'),
('COVID-19 Booster Reminder',
 'Health authorities recommend eligible adults receive their COVID-19 booster dose. Free vaccination camps are available at all government hospitals.',
 DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'low'),
('Cholera Alert — Coastal Regions',
 'Cholera cases have been identified in coastal fishing communities. WHO and local health departments are deploying oral vaccines and water purification tablets.',
 DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'critical');
