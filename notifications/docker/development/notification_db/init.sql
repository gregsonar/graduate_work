DROP SEQUENCE IF EXISTS "public"."ids";
CREATE SEQUENCE "public"."ids"
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

DROP TABLE IF EXISTS "public"."users";
CREATE TABLE "public"."users" (
  "id" uuid PRIMARY KEY,
  "email" TEXT NOT NULL UNIQUE
);

INSERT INTO "public"."users" ("id", "email") VALUES
  ('d6fa8c32-fdce-44cf-9444-9848119c36a3', 'user1@example.com'),
  ('d6fa8c32-fdce-44cf-9444-9848119c36a4', 'user2@example.com'),
  ('d6fa8c32-fdce-44cf-9444-9848119c36a5', 'user3@example.com');

CREATE INDEX "users_id_idx" ON "public"."users"("id");
CREATE INDEX "users_email_idx" ON "public"."users"("email");

DROP TABLE IF EXISTS "public"."notification_messages";
DROP TABLE IF EXISTS "public"."notifications";
CREATE TABLE "public"."notification_messages" (
  "id" uuid PRIMARY KEY,
  "user_id" uuid NOT NULL,
  "film_id" uuid,
  "message" TEXT NOT NULL,
  "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX "notifications_id-idx" ON "public"."notification_messages"("id");

DROP TABLE IF EXISTS "public"."timetable";
CREATE TABLE "public"."timetable" (
  "id" uuid PRIMARY KEY,
  "key" TEXT NOT NULL,
  "min" INTEGER,
  "h" INTEGER,
  "day" INTEGER,
  "month" INTEGER,
  "week_day" INTEGER
);
CREATE INDEX "timetable_id-idx" ON "public"."timetable"("id");

DROP TABLE IF EXISTS "public"."rule";
CREATE TABLE "public"."rule" (
  "id" uuid PRIMARY KEY,
  "timetable_id" uuid NOT NULL,
  "name" TEXT NOT NULL,
  "template" TEXT NOT NULL,
  "subject" TEXT NOT NULL
);
CREATE INDEX "rule_id-idx" ON "public"."rule"("id");