import pytest
from src.cleaner import clean_text_block

def test_clean_form_feed():
    assert clean_text_block("Text\x0cPage break") == "TextPage break"
    assert clean_text_block("Text\fPage break") == "TextPage break"

def test_clean_page_numbers():
    assert clean_text_block("Página 1 de 10") == ""
    assert clean_text_block("pg. 5") == ""
    assert clean_text_block("Conteúdo Página 12") == "Conteúdo"

def test_clean_graph_axis():
    # Sequence of short numbers
    assert clean_text_block("1 2 3 4 5") == ""
    # Should stay if it's not a long sequence (e.g., date or few numbers)
    assert clean_text_block("2024 12 31") == "2024 12 31"
    assert clean_text_block("10 20 30") == "10 20 30"

def test_clean_prices():
    assert clean_text_block("R$ 10,00 R$ 20,00") == ""
    assert clean_text_block("R$ R$ R$") == ""
    assert clean_text_block("10,00 20,00") == ""

def test_clean_hyphenation():
    assert clean_text_block("con-\ntinuo") == "continuo"
    assert clean_text_block("de-\nsolado") == "desolado"

def test_join_broken_sentences():
    assert clean_text_block("Frase que\ncontinua.") == "Frase que continua."
    assert clean_text_block("Frase finalizada.\nNova frase.") == "Frase finalizada.\nNova frase."

def test_clean_repeated_punctuation():
    assert clean_text_block("Erro de extração....") == "Erro de extração."
    assert clean_text_block("O que houve??") == "O que houve?"
