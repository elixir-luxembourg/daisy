from core.importer.base_importer import BaseImporter
from core.models.partner import Partner, SECTOR_CATEGORY
from core.importer.JSONSchemaValidator import InstitutionJSONSchemaValidator


class PartnersImporter(BaseImporter):
    """
       `PartersImporter`, should be able to fill the database with institutions information, based on JSON file
       complying to the schema in:
        https://raw.githubusercontent.com/elixir-luxembourg/json-schemas/master/schemas/elu-institution.json

       Usage example:
           def import_partners():
               importer = PartnersImporter()
               importer.import_json_file("partners.json")
       """

    json_schema_validator = InstitutionJSONSchemaValidator()

    def process_json(self, partner_dict):
        try:
            partner = Partner.objects.get(name=partner_dict.get('name'))
            self.logger.warning(
                f'Partner with name \""{partner_dict.get("name")}"\" already found. It will be updated.')
        except Partner.DoesNotExist:
            self.logger.info(f'Creating institution "{partner_dict.get("name")}")')
            partner = Partner.objects.create(**partner_dict)
        partner.name = partner_dict['name']
        partner.elu_accession = partner_dict['elu_accession']
        partner.is_clinical = partner_dict['is_clinical']
        partner.geo_category = partner_dict['geo_category']
        partner.sector_category = self.process_sector_category(partner_dict)
        partner.address = partner_dict.get('address') if partner_dict.get('address') else ''
        partner.country_code = partner_dict['country_code']
        partner.save()
        partner.updated = True
        if self.publish_on_import:
            self.publish_object(partner)

    @staticmethod
    def process_sector_category(partner_dict):
        sector_category_str = partner_dict.get('sector_category', '')
        return sector_category_str
