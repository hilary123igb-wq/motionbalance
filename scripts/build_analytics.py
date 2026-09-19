import duckdb

con = duckdb.connect("motionbalance.duckdb")
con.execute(open("sql/analytics.sql").read())
con.close()
print("views created")