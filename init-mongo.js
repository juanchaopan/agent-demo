try {
  print("Creating app db user for db: agent_mongo_db...");
  db.getSiblingDB("agent_mongo_db").createUser({
    user: "agent_mongo_user",
    pwd: "mongo_dev_password_123",
    roles: [{ role: "readWrite", db: "agent_mongo_db" }],
  });
  print("App db user created");
} catch (e) {
  printjson(e);
}
