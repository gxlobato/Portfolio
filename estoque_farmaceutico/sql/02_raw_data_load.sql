-- ============================================================================
-- ESTOQUE FARMACÊUTICO — CARGA DE DADOS SINTÉTICOS (RAW)
-- Executar após 01_raw_schema_ddl.sql
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SALAS DE ESTOQUE (10 centros de distribuição)
-- ----------------------------------------------------------------------------
INSERT INTO raw.salas_estoque (sala_id, nome, regiao, cidade, uf, capacidade_m3) VALUES
(1, 'CD São Paulo', 'Sudeste', 'São Paulo', 'SP', 1811.26),
(2, 'CD Rio de Janeiro', 'Sudeste', 'Rio de Janeiro', 'RJ', 3366.93),
(3, 'CD Belo Horizonte', 'Sudeste', 'Belo Horizonte', 'MG', 2776.38),
(4, 'CD Curitiba', 'Sul', 'Curitiba', 'PR', 2416.38),
(5, 'CD Porto Alegre', 'Sul', 'Porto Alegre', 'RS', 1221.25),
(6, 'CD Recife', 'Nordeste', 'Recife', 'PE', 1221.19),
(7, 'CD Salvador', 'Nordeste', 'Salvador', 'BA', 956.83),
(8, 'CD Goiânia', 'Centro-Oeste', 'Goiânia', 'GO', 3138.68),
(9, 'CD Manaus', 'Norte', 'Manaus', 'AM', 2423.01),
(10, 'CD Brasília', 'Centro-Oeste', 'Brasília', 'DF', 2711.80);

-- ----------------------------------------------------------------------------
-- 2. MEDICAMENTOS (20 itens, 8 categorias terapêuticas)
-- ----------------------------------------------------------------------------
INSERT INTO raw.medicamentos (medicamento_id, nome, categoria, fabricante, principio_ativo, preco_unitario, validade_dias_padrao, armazenamento_refrigerado) VALUES
(1, 'Loratadina 10mg', 'Antialérgico', 'Cristália', 'Loratadina', 8.10, 540, FALSE),
(2, 'Desloratadina 5mg', 'Antialérgico', 'Cristália', 'Desloratadina', 3.56, 365, FALSE),
(3, 'Cetirizina 10mg', 'Antialérgico', 'EMS', 'Cetirizina', 28.30, 540, FALSE),
(4, 'Paracetamol 750mg', 'Analgésico/Antitérmico', 'Hypera', 'Paracetamol', 38.70, 365, FALSE),
(5, 'Dipirona Sódica 500mg', 'Analgésico/Antitérmico', 'Medley', 'Dipirona', 53.37, 540, FALSE),
(6, 'Ibuprofeno 600mg', 'Anti-inflamatório', 'Pfizer', 'Ibuprofeno', 27.31, 730, FALSE),
(7, 'Amoxicilina 500mg', 'Antibiótico', 'Cristália', 'Amoxicilina', 10.88, 540, FALSE),
(8, 'Azitromicina 500mg', 'Antibiótico', 'Medley', 'Azitromicina', 34.67, 365, FALSE),
(9, 'Dextrometorfano Xarope', 'Antitussígeno', 'Medley', 'Dextrometorfano', 73.59, 730, FALSE),
(10, 'Ambroxol Xarope', 'Expectorante', 'Hypera', 'Ambroxol', 40.22, 540, FALSE),
(11, 'Omeprazol 20mg', 'Antiulceroso', 'Aché', 'Omeprazol', 80.29, 540, FALSE),
(12, 'Losartana Potássica 50mg', 'Anti-hipertensivo', 'Eurofarma', 'Losartana', 34.91, 540, FALSE),
(13, 'Metformina 850mg', 'Antidiabético', 'Hypera', 'Metformina', 22.32, 730, FALSE),
(14, 'Sinvastatina 20mg', 'Hipolipemiante', 'Aché', 'Sinvastatina', 13.45, 365, FALSE),
(15, 'Levotiroxina 50mcg', 'Hormonal', 'Pfizer', 'Levotiroxina', 6.30, 540, FALSE),
(16, 'Insulina NPH 100UI/mL', 'Antidiabético', 'EMS', 'Insulina', 24.59, 180, TRUE),
(17, 'Vacina Influenza', 'Imunobiológico', 'Pfizer', 'Vacina', 65.06, 180, TRUE),
(18, 'Soro Fisiológico 0,9% 500mL', 'Solução Parenteral', 'Cristália', 'Soro', 45.89, 540, FALSE),
(19, 'Hidroclorotiazida 25mg', 'Diurético', 'Aché', 'Hidroclorotiazida', 18.57, 730, FALSE),
(20, 'Fluconazol 150mg', 'Antifúngico', 'Eurofarma', 'Fluconazol', 66.67, 540, FALSE);

-- ----------------------------------------------------------------------------
-- 3. CLIENTES (200 farmácias/hospitais/clínicas/UPAs/drogarias)
-- Gerados sinteticamente com Faker (pt_BR), distribuídos entre as 10 salas.
-- ----------------------------------------------------------------------------
INSERT INTO raw.clientes (cliente_id, nome, tipo_cliente, cidade, uf, sala_id_principal) VALUES
(1, 'Alves e Filhos', 'Drogaria Popular', 'Brasília', 'DF', 10),
(2, 'da Cruz', 'Hospital', 'Goiânia', 'GO', 8),
(3, 'Carvalho Sousa S/A', 'UPA', 'Manaus', 'AM', 9),
(4, 'Pastor - ME', 'Farmácia', 'Porto Alegre', 'RS', 5),
(5, 'Alves S/A', 'Hospital', 'Rio de Janeiro', 'RJ', 2),
(6, 'da Conceição Montenegro - EI', 'Farmácia', 'Goiânia', 'GO', 8),
(7, 'Novais S.A.', 'Farmácia', 'Manaus', 'AM', 9),
(8, 'Câmara', 'Farmácia', 'São Paulo', 'SP', 1),
(9, 'Pastor', 'Clínica', 'Manaus', 'AM', 9),
(10, 'Abreu', 'Farmácia', 'Goiânia', 'GO', 8),
(11, 'Sampaio Lima Ltda.', 'Clínica', 'Belo Horizonte', 'MG', 3),
(12, 'Cassiano', 'Clínica', 'Belo Horizonte', 'MG', 3),
(13, 'Teixeira Fernandes S/A', 'Drogaria Popular', 'Porto Alegre', 'RS', 5),
(14, 'Garcia S/A', 'Farmácia', 'Brasília', 'DF', 10),
(15, 'Ferreira', 'Drogaria Popular', 'Salvador', 'BA', 7),
(16, 'Aparecida', 'Farmácia', 'Rio de Janeiro', 'RJ', 2),
(17, 'Nascimento', 'Farmácia', 'Salvador', 'BA', 7),
(18, 'Garcia S/A', 'Clínica', 'Goiânia', 'GO', 8),
(19, 'Pires', 'Farmácia', 'Goiânia', 'GO', 8),
(20, 'Oliveira', 'Hospital', 'Belo Horizonte', 'MG', 3),
(21, 'Santos Azevedo S/A', 'UPA', 'Porto Alegre', 'RS', 5),
(22, 'Vargas da Rocha S/A', 'Clínica', 'Belo Horizonte', 'MG', 3),
(23, 'Brito Garcia Ltda.', 'Farmácia', 'Brasília', 'DF', 10),
(24, 'Porto', 'Farmácia', 'Salvador', 'BA', 7),
(25, 'Castro', 'Farmácia', 'Brasília', 'DF', 10),
(26, 'Fogaça', 'Farmácia', 'Belo Horizonte', 'MG', 3),
(27, 'Rios da Mata e Filhos', 'Hospital', 'Salvador', 'BA', 7),
(28, 'Pereira e Filhos', 'Drogaria Popular', 'Curitiba', 'PR', 4),
(29, 'Nascimento Siqueira S.A.', 'Clínica', 'Salvador', 'BA', 7),
(30, 'Martins Garcia Ltda.', 'Drogaria Popular', 'Curitiba', 'PR', 4),
(31, 'Rodrigues Duarte S/A', 'Farmácia', 'Salvador', 'BA', 7),
(32, 'Andrade Dias - ME', 'Drogaria Popular', 'Recife', 'PE', 6),
(33, 'Azevedo', 'Drogaria Popular', 'Brasília', 'DF', 10),
(34, 'Nunes Silva Ltda.', 'Farmácia', 'Manaus', 'AM', 9),
(35, 'Rezende Monteiro - ME', 'Drogaria Popular', 'Curitiba', 'PR', 4),
(36, 'Casa Grande', 'Farmácia', 'Brasília', 'DF', 10),
(37, 'Carvalho', 'Farmácia', 'Manaus', 'AM', 9),
(38, 'Souza Novais - EI', 'Farmácia', 'São Paulo', 'SP', 1),
(39, 'Souza', 'Drogaria Popular', 'Manaus', 'AM', 9),
(40, 'Pacheco', 'Farmácia', 'Manaus', 'AM', 9),
(41, 'Fonseca', 'Hospital', 'Recife', 'PE', 6),
(42, 'Carvalho Moraes - ME', 'Hospital', 'Manaus', 'AM', 9),
(43, 'Sá S/A', 'Farmácia', 'São Paulo', 'SP', 1),
(44, 'Cassiano e Filhos', 'Drogaria Popular', 'Goiânia', 'GO', 8),
(45, 'Vieira Rodrigues - ME', 'Farmácia', 'Recife', 'PE', 6),
(46, 'Gomes - ME', 'Clínica', 'Goiânia', 'GO', 8),
(47, 'Moura', 'Farmácia', 'São Paulo', 'SP', 1),
(48, 'Novaes', 'UPA', 'Brasília', 'DF', 10),
(49, 'Rodrigues e Filhos', 'Hospital', 'Salvador', 'BA', 7),
(50, 'Rodrigues - EI', 'Farmácia', 'São Paulo', 'SP', 1),
(51, 'Vargas', 'Farmácia', 'Goiânia', 'GO', 8),
(52, 'Camargo', 'UPA', 'São Paulo', 'SP', 1),
(53, 'Lopes', 'Farmácia', 'Recife', 'PE', 6),
(54, 'Marques Abreu e Filhos', 'Clínica', 'São Paulo', 'SP', 1),
(55, 'Montenegro', 'Hospital', 'Rio de Janeiro', 'RJ', 2),
(56, 'Montenegro Caldeira e Filhos', 'UPA', 'Brasília', 'DF', 10),
(57, 'Porto', 'Clínica', 'Salvador', 'BA', 7),
(58, 'Cassiano Freitas S.A.', 'Farmácia', 'Goiânia', 'GO', 8),
(59, 'Peixoto Ltda.', 'Farmácia', 'Recife', 'PE', 6),
(60, 'Almeida', 'UPA', 'Curitiba', 'PR', 4),
(61, 'Fonseca Ltda.', 'Hospital', 'Recife', 'PE', 6),
(62, 'Araújo da Costa - EI', 'Farmácia', 'São Paulo', 'SP', 1),
(63, 'Barros e Filhos', 'Clínica', 'Recife', 'PE', 6),
(64, 'Azevedo', 'Hospital', 'Belo Horizonte', 'MG', 3),
(65, 'Cardoso Ribeiro - ME', 'Farmácia', 'Curitiba', 'PR', 4),
(66, 'da Luz Moura - EI', 'Drogaria Popular', 'Belo Horizonte', 'MG', 3),
(67, 'Cunha', 'Clínica', 'Curitiba', 'PR', 4),
(68, 'Silva das Neves - ME', 'Drogaria Popular', 'Curitiba', 'PR', 4),
(69, 'Macedo', 'Farmácia', 'Goiânia', 'GO', 8),
(70, 'Campos', 'Drogaria Popular', 'Rio de Janeiro', 'RJ', 2),
(71, 'Câmara Azevedo Ltda.', 'Farmácia', 'Manaus', 'AM', 9),
(72, 'Pastor - EI', 'Hospital', 'Salvador', 'BA', 7),
(73, 'Pastor Câmara S/A', 'Farmácia', 'Brasília', 'DF', 10),
(74, 'Santos e Filhos', 'UPA', 'Brasília', 'DF', 10),
(75, 'da Conceição S/A', 'Hospital', 'Curitiba', 'PR', 4),
(76, 'Farias S/A', 'UPA', 'Rio de Janeiro', 'RJ', 2),
(77, 'da Mota Rios - ME', 'Drogaria Popular', 'Porto Alegre', 'RS', 5),
(78, 'Nogueira Cardoso e Filhos', 'Farmácia', 'Salvador', 'BA', 7),
(79, 'da Cruz', 'Clínica', 'Belo Horizonte', 'MG', 3),
(80, 'Jesus', 'Drogaria Popular', 'Belo Horizonte', 'MG', 3),
(81, 'Brito Brito e Filhos', 'Clínica', 'Recife', 'PE', 6),
(82, 'Fogaça', 'Drogaria Popular', 'Goiânia', 'GO', 8),
(83, 'Jesus', 'Farmácia', 'São Paulo', 'SP', 1),
(84, 'Siqueira', 'Clínica', 'Recife', 'PE', 6),
(85, 'Rocha e Filhos', 'Farmácia', 'Belo Horizonte', 'MG', 3),
(86, 'Araújo - ME', 'Clínica', 'Manaus', 'AM', 9),
(87, 'Caldeira', 'Farmácia', 'Rio de Janeiro', 'RJ', 2),
(88, 'Correia Correia - EI', 'Hospital', 'Rio de Janeiro', 'RJ', 2),
(89, 'Carvalho', 'Clínica', 'Belo Horizonte', 'MG', 3),
(90, 'Cirino', 'Farmácia', 'Manaus', 'AM', 9),
(91, 'Martins', 'Farmácia', 'Curitiba', 'PR', 4),
(92, 'Barbosa Macedo - EI', 'Farmácia', 'Porto Alegre', 'RS', 5),
(93, 'Aragão e Filhos', 'Clínica', 'Goiânia', 'GO', 8),
(94, 'Borges S.A.', 'Clínica', 'Salvador', 'BA', 7),
(95, 'Jesus Mendonça - ME', 'Hospital', 'São Paulo', 'SP', 1),
(96, 'Guerra Araújo S.A.', 'Clínica', 'Belo Horizonte', 'MG', 3),
(97, 'Abreu', 'Farmácia', 'Recife', 'PE', 6),
(98, 'da Luz', 'UPA', 'Recife', 'PE', 6),
(99, 'da Paz', 'Drogaria Popular', 'Belo Horizonte', 'MG', 3),
(100, 'Sampaio', 'Farmácia', 'Rio de Janeiro', 'RJ', 2),
(101, 'Cassiano', 'Hospital', 'São Paulo', 'SP', 1),
(102, 'da Rocha Cunha S/A', 'Farmácia', 'São Paulo', 'SP', 1),
(103, 'Souza Ltda.', 'Hospital', 'Belo Horizonte', 'MG', 3),
(104, 'Aragão - EI', 'Farmácia', 'São Paulo', 'SP', 1),
(105, 'Montenegro', 'Drogaria Popular', 'Porto Alegre', 'RS', 5),
(106, 'Araújo Moraes S/A', 'UPA', 'Manaus', 'AM', 9),
(107, 'Azevedo Peixoto S/A', 'Hospital', 'São Paulo', 'SP', 1),
(108, 'Guerra Campos - EI', 'UPA', 'Belo Horizonte', 'MG', 3),
(109, 'Pacheco Peixoto S/A', 'Farmácia', 'Curitiba', 'PR', 4),
(110, 'Leão e Filhos', 'Farmácia', 'Porto Alegre', 'RS', 5),
(111, 'da Luz', 'Farmácia', 'São Paulo', 'SP', 1),
(112, 'Rios Silva Ltda.', 'Hospital', 'Rio de Janeiro', 'RJ', 2),
(113, 'da Luz Gonçalves S.A.', 'Clínica', 'Recife', 'PE', 6),
(114, 'Marques', 'Farmácia', 'Goiânia', 'GO', 8),
(115, 'Sá', 'Clínica', 'Rio de Janeiro', 'RJ', 2),
(116, 'Albuquerque - ME', 'Farmácia', 'Recife', 'PE', 6),
(117, 'Barbosa - EI', 'Drogaria Popular', 'Brasília', 'DF', 10),
(118, 'Montenegro da Luz S.A.', 'Drogaria Popular', 'São Paulo', 'SP', 1),
(119, 'Azevedo', 'Clínica', 'Manaus', 'AM', 9),
(120, 'Freitas da Paz S.A.', 'Farmácia', 'Salvador', 'BA', 7),
(121, 'Nogueira', 'Farmácia', 'Salvador', 'BA', 7),
(122, 'Pimenta', 'Drogaria Popular', 'Rio de Janeiro', 'RJ', 2),
(123, 'Rios - EI', 'Farmácia', 'Brasília', 'DF', 10),
(124, 'Ribeiro', 'Clínica', 'Curitiba', 'PR', 4),
(125, 'Carvalho Ltda.', 'Farmácia', 'São Paulo', 'SP', 1),
(126, 'Caldeira e Filhos', 'Farmácia', 'Belo Horizonte', 'MG', 3),
(127, 'da Mata da Paz - EI', 'Farmácia', 'Rio de Janeiro', 'RJ', 2),
(128, 'Silva Fernandes S.A.', 'Clínica', 'Salvador', 'BA', 7),
(129, 'Montenegro', 'Hospital', 'Belo Horizonte', 'MG', 3),
(130, 'da Cunha', 'Hospital', 'Recife', 'PE', 6),
(131, 'Borges e Filhos', 'Farmácia', 'Recife', 'PE', 6),
(132, 'da Mota', 'Drogaria Popular', 'Brasília', 'DF', 10),
(133, 'Abreu Ltda.', 'Hospital', 'Recife', 'PE', 6),
(134, 'Porto da Luz S.A.', 'Hospital', 'Porto Alegre', 'RS', 5),
(135, 'Novaes', 'Farmácia', 'Porto Alegre', 'RS', 5),
(136, 'Novais', 'Hospital', 'Porto Alegre', 'RS', 5),
(137, 'Camargo S/A', 'Farmácia', 'Recife', 'PE', 6),
(138, 'Nogueira Andrade Ltda.', 'Farmácia', 'Curitiba', 'PR', 4),
(139, 'Lopes Cardoso S/A', 'Clínica', 'Belo Horizonte', 'MG', 3),
(140, 'Fonseca', 'Farmácia', 'Curitiba', 'PR', 4),
(141, 'Fogaça S.A.', 'Hospital', 'Rio de Janeiro', 'RJ', 2),
(142, 'Rios Caldeira Ltda.', 'Clínica', 'Belo Horizonte', 'MG', 3),
(143, 'Pinto', 'Farmácia', 'Belo Horizonte', 'MG', 3),
(144, 'da Costa Castro S.A.', 'Farmácia', 'Salvador', 'BA', 7),
(145, 'Alves', 'UPA', 'Brasília', 'DF', 10),
(146, 'Sousa Farias - ME', 'Farmácia', 'Salvador', 'BA', 7),
(147, 'da Mata Castro e Filhos', 'Farmácia', 'Porto Alegre', 'RS', 5),
(148, 'Garcia S/A', 'Farmácia', 'Brasília', 'DF', 10),
(149, 'Câmara', 'Farmácia', 'Rio de Janeiro', 'RJ', 2),
(150, 'Marques Ferreira Ltda.', 'Clínica', 'Recife', 'PE', 6),
(151, 'Câmara Alves e Filhos', 'Drogaria Popular', 'Goiânia', 'GO', 8),
(152, 'Guerra Farias Ltda.', 'UPA', 'São Paulo', 'SP', 1),
(153, 'Vargas Ltda.', 'Clínica', 'Salvador', 'BA', 7),
(154, 'Ramos', 'Clínica', 'Porto Alegre', 'RS', 5),
(155, 'Rocha', 'Farmácia', 'Salvador', 'BA', 7),
(156, 'Alves', 'Farmácia', 'Brasília', 'DF', 10),
(157, 'da Luz S.A.', 'Farmácia', 'Porto Alegre', 'RS', 5),
(158, 'Andrade', 'Farmácia', 'Porto Alegre', 'RS', 5),
(159, 'Peixoto - ME', 'Farmácia', 'Curitiba', 'PR', 4),
(160, 'Siqueira', 'Clínica', 'Brasília', 'DF', 10),
(161, 'Lopes', 'Hospital', 'Porto Alegre', 'RS', 5),
(162, 'Gomes - EI', 'Hospital', 'São Paulo', 'SP', 1),
(163, 'da Cunha Aparecida e Filhos', 'Farmácia', 'Porto Alegre', 'RS', 5),
(164, 'Abreu', 'Drogaria Popular', 'Brasília', 'DF', 10),
(165, 'Fonseca Lopes S/A', 'Farmácia', 'Curitiba', 'PR', 4),
(166, 'Pinto', 'Clínica', 'Brasília', 'DF', 10),
(167, 'Ribeiro', 'Hospital', 'Brasília', 'DF', 10),
(168, 'Silveira Ltda.', 'Clínica', 'Goiânia', 'GO', 8),
(169, 'Rios', 'Clínica', 'Curitiba', 'PR', 4),
(170, 'Duarte', 'Drogaria Popular', 'Salvador', 'BA', 7),
(171, 'Sampaio', 'Hospital', 'Curitiba', 'PR', 4),
(172, 'Novaes', 'Hospital', 'Rio de Janeiro', 'RJ', 2),
(173, 'Correia Leão e Filhos', 'Hospital', 'São Paulo', 'SP', 1),
(174, 'Rocha', 'Drogaria Popular', 'Belo Horizonte', 'MG', 3),
(175, 'Pimenta Nunes Ltda.', 'Drogaria Popular', 'Belo Horizonte', 'MG', 3),
(176, 'Novaes', 'Drogaria Popular', 'Goiânia', 'GO', 8),
(177, 'da Rosa Ltda.', 'Farmácia', 'Rio de Janeiro', 'RJ', 2),
(178, 'Lopes Viana - EI', 'Clínica', 'Rio de Janeiro', 'RJ', 2),
(179, 'Martins', 'Clínica', 'São Paulo', 'SP', 1),
(180, 'Macedo', 'Clínica', 'Brasília', 'DF', 10),
(181, 'Moraes Melo e Filhos', 'Farmácia', 'Rio de Janeiro', 'RJ', 2),
(182, 'Ribeiro Barros Ltda.', 'Farmácia', 'Salvador', 'BA', 7),
(183, 'Borges', 'Farmácia', 'Porto Alegre', 'RS', 5),
(184, 'Rocha das Neves S.A.', 'Clínica', 'Goiânia', 'GO', 8),
(185, 'Casa Grande Alves S/A', 'UPA', 'Porto Alegre', 'RS', 5),
(186, 'Melo Pimenta S/A', 'Farmácia', 'Curitiba', 'PR', 4),
(187, 'Leão', 'Hospital', 'Manaus', 'AM', 9),
(188, 'Silva Sampaio - ME', 'UPA', 'Belo Horizonte', 'MG', 3),
(189, 'Guerra', 'Farmácia', 'Curitiba', 'PR', 4),
(190, 'Casa Grande Rezende e Filhos', 'Hospital', 'Salvador', 'BA', 7),
(191, 'Sá S/A', 'Drogaria Popular', 'Salvador', 'BA', 7),
(192, 'Câmara', 'Farmácia', 'Porto Alegre', 'RS', 5),
(193, 'Sampaio Moreira - ME', 'Clínica', 'Salvador', 'BA', 7),
(194, 'Novais S.A.', 'Farmácia', 'Manaus', 'AM', 9),
(195, 'Marques S.A.', 'Hospital', 'São Paulo', 'SP', 1),
(196, 'Rios', 'Drogaria Popular', 'Curitiba', 'PR', 4),
(197, 'Sá', 'Farmácia', 'Recife', 'PE', 6),
(198, 'Pimenta', 'Farmácia', 'Belo Horizonte', 'MG', 3),
(199, 'Novaes', 'Drogaria Popular', 'Manaus', 'AM', 9),
(200, 'Castro', 'Farmácia', 'Manaus', 'AM', 9);

-- ----------------------------------------------------------------------------
-- 4. LOTES + MOVIMENTAÇÃO SEMANAL DE ESTOQUE
-- Gerados inteiramente no servidor via bloco PL/pgSQL — simula 5 anos
-- (260 semanas) de demanda sazonal, política de reposição (ponto de
-- pedido, lead time, estoque de segurança) e taxa de ruptura realista.
-- ----------------------------------------------------------------------------
DO $$
DECLARE
  sala RECORD;
  med RECORD;
  semana_idx INT;
  data_inicio DATE := '2021-06-29';
  semana_ref DATE;
  porte_sala NUMERIC;
  demanda_base NUMERIC;
  tendencia_anual NUMERIC;
  lead_time INT;
  estoque_seguranca NUMERIC;
  ponto_reposicao NUMERIC;
  lote_tamanho NUMERIC;
  saldo NUMERIC;
  saldo_inicial INT;
  entradas INT;
  saidas INT;
  saldo_final INT;
  ruptura BOOLEAN;
  pedido_pendente INT;
  mov_id BIGINT := 1;
  lote_id INT := 1;
  fs NUMERIC;
  tend NUMERIC;
  ruido NUMERIC;
  mes INT;
  ano INT;
  semana_numero INT;
  n_lotes_iniciais INT;
  i INT;
  data_fab DATE;
  validade_dias INT;
BEGIN
  FOR sala IN SELECT sala_id FROM raw.salas_estoque ORDER BY sala_id LOOP
    porte_sala := 0.7 + random()*0.7;
    FOR med IN
      SELECT medicamento_id, validade_dias_padrao,
             CASE
               WHEN categoria = 'Antialérgico' THEN 'primavera'
               WHEN nome = 'Fluconazol 150mg' THEN 'verao'
               WHEN nome = 'Vacina Influenza' THEN 'outono'
               WHEN categoria IN ('Antiulceroso','Anti-hipertensivo','Antidiabético','Hipolipemiante','Hormonal','Diurético') THEN 'estavel'
               ELSE 'inverno'
             END AS saz
      FROM raw.medicamentos ORDER BY medicamento_id
    LOOP
      demanda_base := (40 + random()*180) * porte_sala;
      tendencia_anual := -0.03 + random()*0.10;
      lead_time := 1 + floor(random()*3)::int;
      estoque_seguranca := demanda_base * 1.5;
      ponto_reposicao := demanda_base * lead_time + estoque_seguranca;
      lote_tamanho := demanda_base * (4 + random()*4);
      saldo := ponto_reposicao + lote_tamanho * (0.5 + random()*0.5);

      n_lotes_iniciais := 2 + floor(random()*3)::int;
      FOR i IN 1..n_lotes_iniciais LOOP
        data_fab := data_inicio - (floor(random()*190)+10)::int;
        validade_dias := med.validade_dias_padrao;
        INSERT INTO raw.lotes (lote_id, medicamento_id, sala_id, data_fabricacao, data_validade, quantidade_inicial)
        VALUES (lote_id, med.medicamento_id, sala.sala_id, data_fab, data_fab + validade_dias, (lote_tamanho*(0.5+random()*0.7))::int);
        lote_id := lote_id + 1;
      END LOOP;

      pedido_pendente := 0;

      FOR semana_idx IN 0..259 LOOP
        semana_ref := data_inicio + (semana_idx*7);
        ano := EXTRACT(YEAR FROM semana_ref)::int;
        semana_numero := EXTRACT(WEEK FROM semana_ref)::int;
        mes := EXTRACT(MONTH FROM semana_ref)::int;

        fs := CASE
          WHEN med.saz = 'inverno' AND mes IN (6,7,8) THEN 1.55
          WHEN med.saz = 'primavera' AND mes IN (9,10,11) THEN 1.55
          WHEN med.saz = 'verao' AND mes IN (12,1,2) THEN 1.55
          WHEN med.saz = 'outono' AND mes IN (4,5) THEN 1.55
          WHEN med.saz = 'estavel' THEN 1.0
          ELSE 0.80
        END;

        tend := power(1+tendencia_anual, semana_idx/52.0);
        ruido := 1.0 + (random()-0.5)*0.3;
        saidas := round(demanda_base * fs * tend * ruido)::int;
        IF saidas < 0 THEN saidas := 0; END IF;

        saldo_inicial := round(saldo)::int;
        entradas := 0;

        IF saldo_inicial <= ponto_reposicao AND pedido_pendente = 0 THEN
          pedido_pendente := lead_time;
        END IF;

        IF pedido_pendente > 0 THEN
          pedido_pendente := pedido_pendente - 1;
          IF pedido_pendente = 0 THEN
            entradas := round(lote_tamanho * (0.85 + random()*0.3))::int;
            validade_dias := med.validade_dias_padrao;
            INSERT INTO raw.lotes (lote_id, medicamento_id, sala_id, data_fabricacao, data_validade, quantidade_inicial)
            VALUES (lote_id, med.medicamento_id, sala.sala_id, semana_ref, semana_ref + validade_dias, entradas);
            lote_id := lote_id + 1;
          END IF;
        END IF;

        saldo_final := saldo_inicial + entradas - saidas;
        ruptura := saldo_final < 0;
        IF ruptura THEN
          saidas := saidas + saldo_final;
          saldo_final := 0;
        END IF;

        INSERT INTO raw.estoque_movimentacao_semanal
          (id, sala_id, medicamento_id, semana_referencia, ano, semana_numero, saldo_inicial, entradas, saidas, saldo_final, ruptura_estoque)
        VALUES
          (mov_id, sala.sala_id, med.medicamento_id, semana_ref, ano, semana_numero, saldo_inicial, entradas, saidas, saldo_final, ruptura);

        mov_id := mov_id + 1;
        saldo := saldo_final;
      END LOOP;
    END LOOP;
  END LOOP;
END $$;
