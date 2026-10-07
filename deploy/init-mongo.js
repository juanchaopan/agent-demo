db.getSiblingDB("agent_mongo_db").createUser({
  user: "agent_mongo_user",
  pwd: process.env.MONGO_DB_PASSWORD,
  roles: [{ role: "readWrite", db: "agent_mongo_db" }],
});
