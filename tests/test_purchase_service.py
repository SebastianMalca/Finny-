"""
test_purchase_service.py — Pruebas Unitarias de PurchaseService.

Cubre:
  - validate: todos los campos requeridos, límites de monto, categorías
  - create: creación exitosa con side-effects de gamificación
  - get_all / get_by_id / delete: operaciones CRUD
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.services.purchase_service import PurchaseService


class TestPurchaseValidation:
    """Pruebas del método PurchaseService.validate."""

    def test_validate_none_body_returns_error(self):
        err = PurchaseService.validate(None)
        assert err is not None
        assert 'JSON' in err

    def test_validate_empty_name(self):
        err = PurchaseService.validate({'name': '', 'amount': 10.0})
        assert err is not None
        assert 'name' in err.lower()

    def test_validate_name_whitespace_only(self):
        err = PurchaseService.validate({'name': '   ', 'amount': 10.0})
        assert err is not None

    def test_validate_name_too_long(self):
        long_name = 'A' * 101
        err = PurchaseService.validate({'name': long_name, 'amount': 10.0})
        assert err is not None
        assert 'nombre' in err.lower() or '100' in err

    def test_validate_missing_amount(self):
        err = PurchaseService.validate({'name': 'Coffee'})
        assert err is not None
        assert 'amount' in err.lower()

    def test_validate_amount_not_a_number(self):
        err = PurchaseService.validate({'name': 'Coffee', 'amount': 'abc'})
        assert err is not None
        assert 'número' in err.lower()

    def test_validate_amount_zero(self):
        err = PurchaseService.validate({'name': 'Coffee', 'amount': 0})
        assert err is not None
        assert 'mayor' in err.lower() or '0' in err

    def test_validate_amount_negative(self):
        err = PurchaseService.validate({'name': 'Coffee', 'amount': -5.0})
        assert err is not None

    def test_validate_amount_exceeds_max(self):
        err = PurchaseService.validate({'name': 'House', 'amount': 2_000_000})
        assert err is not None
        assert '1,000,000' in err or 'superar' in err.lower()

    def test_validate_invalid_category(self):
        err = PurchaseService.validate({'name': 'Test', 'amount': 10.0, 'category': 'InvalidCat'})
        assert err is not None
        assert 'categoría' in err.lower() or 'Categoría' in err

    def test_validate_valid_category(self):
        for cat in ['Food', 'Transport', 'Study', 'Entertainment', 'Health', 'Other']:
            err = PurchaseService.validate({'name': 'Test', 'amount': 10.0, 'category': cat})
            assert err is None, f"Categoría válida rechazada: {cat}"

    def test_validate_no_category_is_ok(self):
        err = PurchaseService.validate({'name': 'Coffee', 'amount': 5.0})
        assert err is None

    def test_validate_valid_purchase(self):
        err = PurchaseService.validate({'name': 'Lunch', 'amount': 12.50, 'category': 'Food'})
        assert err is None

    def test_validate_amount_as_string_number(self):
        """Amounts que vienen como strings deben ser aceptados si son numéricos."""
        err = PurchaseService.validate({'name': 'Taxi', 'amount': '25.00'})
        assert err is None

    def test_validate_amount_at_boundary_max(self):
        err = PurchaseService.validate({'name': 'Max', 'amount': 1_000_000})
        assert err is None  # igual a max es válido

    def test_validate_amount_above_boundary(self):
        err = PurchaseService.validate({'name': 'OverMax', 'amount': 1_000_001})
        assert err is not None


class TestPurchaseCreate:
    """Pruebas del método PurchaseService.create."""

    def test_create_returns_dict(self):
        mock_purchase = MagicMock()
        mock_purchase.to_dict.return_value = {
            'id': 1, 'name': 'Coffee', 'amount': 3.5, 'category': 'Food'
        }
        with patch('backend.services.purchase_service.PurchaseRepository.create', return_value=mock_purchase), \
             patch('backend.services.purchase_service.GamificationService.on_new_purchase'):
            result = PurchaseService.create(1, {'name': 'Coffee', 'amount': 3.5, 'category': 'Food'})
        assert isinstance(result, dict)
        assert result['name'] == 'Coffee'

    def test_create_triggers_gamification(self):
        mock_purchase = MagicMock()
        mock_purchase.to_dict.return_value = {}
        with patch('backend.services.purchase_service.PurchaseRepository.create', return_value=mock_purchase) as _mock_create, \
             patch('backend.services.purchase_service.GamificationService.on_new_purchase') as mock_gamif:
            PurchaseService.create(1, {'name': 'Test', 'amount': 10.0, 'category': 'Food'})
        mock_gamif.assert_called_once_with(1)

    def test_create_default_category_is_other(self):
        mock_purchase = MagicMock()
        mock_purchase.to_dict.return_value = {}
        with patch('backend.services.purchase_service.PurchaseRepository.create', return_value=mock_purchase) as mock_repo, \
             patch('backend.services.purchase_service.GamificationService.on_new_purchase'):
            PurchaseService.create(1, {'name': 'Mystery', 'amount': 5.0})
        # el tercer argumento del create es category
        call_args = mock_repo.call_args
        assert call_args[0][3] == 'Other' or call_args[1].get('category') == 'Other'

    def test_create_rounds_amount_to_two_decimals(self):
        mock_purchase = MagicMock()
        mock_purchase.to_dict.return_value = {}
        with patch('backend.services.purchase_service.PurchaseRepository.create', return_value=mock_purchase) as mock_repo, \
             patch('backend.services.purchase_service.GamificationService.on_new_purchase'):
            PurchaseService.create(1, {'name': 'Rounding test', 'amount': 3.14159})
        call_args = mock_repo.call_args[0]
        assert call_args[2] == round(3.14159, 2)


class TestPurchaseCRUD:
    """Pruebas de las operaciones de lectura y eliminación."""

    def test_get_all_returns_list(self):
        mock_p1 = MagicMock()
        mock_p1.to_dict.return_value = {'id': 1}
        mock_p2 = MagicMock()
        mock_p2.to_dict.return_value = {'id': 2}
        with patch('backend.services.purchase_service.PurchaseRepository.find_all', return_value=[mock_p1, mock_p2]):
            result = PurchaseService.get_all(user_id=1)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_get_by_id_found(self):
        mock_p = MagicMock()
        mock_p.to_dict.return_value = {'id': 5}
        with patch('backend.services.purchase_service.PurchaseRepository.find_by_id', return_value=mock_p):
            result = PurchaseService.get_by_id(1, 5)
        assert result == {'id': 5}

    def test_get_by_id_not_found(self):
        with patch('backend.services.purchase_service.PurchaseRepository.find_by_id', return_value=None):
            result = PurchaseService.get_by_id(1, 999)
        assert result is None

    def test_delete_existing_purchase(self):
        mock_p = MagicMock()
        with patch('backend.services.purchase_service.PurchaseRepository.find_by_id', return_value=mock_p), \
             patch('backend.services.purchase_service.PurchaseRepository.delete', return_value=True):
            result = PurchaseService.delete(1, 1)
        assert result is True

    def test_delete_nonexistent_purchase(self):
        with patch('backend.services.purchase_service.PurchaseRepository.find_by_id', return_value=None):
            result = PurchaseService.delete(1, 999)
        assert result is False
