-- Peliqan "My Queries".kpi_intercompany (table_id 1416724), stand 2026-11-12
SELECT * FROM (VALUES
 ('acco','WAREHOUSE','AWC','Amsterdam Warehouse Company als klant van ACC','voorstel'),
 ('acco','AMSTERDAM','AFC','Amsterdam Freight Company als klant van ACC','voorstel'),
 ('pgl1','AWC','AWC','Amsterdam Warehouse Company als klant van AFC','voorstel'),
 ('pgl1','CUSTOMS','ACC','Amsterdam Customs Company als klant van AFC','voorstel'),
 ('alaw','FREIGHT','AFC','Amsterdam Freight Company als klant van AWC','voorstel'),
 ('alaw','CUSTOMS','ACC','Amsterdam Custom Company als klant van AWC','voorstel')
) v(admin_code, zoek, tegenpartij, toelichting, status)
