DROP SEQUENCE IF EXISTS "public"."ids";
CREATE SEQUENCE "public"."ids"
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;


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