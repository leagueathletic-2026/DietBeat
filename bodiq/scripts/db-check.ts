import postgres from "postgres";

async function main() {
  const sql = postgres(process.env.DATABASE_URL!, { max: 1 });
  const [r] = await sql`select current_database() as db,
    (select count(*) from pg_extension where extname in ('pg_trgm','unaccent','pgcrypto','citext')) as extensions`;
  console.log(r);
  await sql.end();
}
main();
