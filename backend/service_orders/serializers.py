fromoriginal_specialist_name rest_framework import serializers
from .models import *


class ServiceOrderDetailSerializer(serializers.ModelSerializer):
    remaining_man_days = serializers.ReadOnlyField()
    has_been_extended = serializers.ReadOnlyField()
    has_been_substituted = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    can_request_extension = serializers.SerializerMethodField()
    can_request_substitution = serializers.SerializerMethodField()
    # extensions_count = serializers.SerializerMethodField()
    # substitutions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceOrder
        fields = '__all__'
    
    def get_can_request_extension(self, obj):
        return obj.can_request_extension()
    
    def get_can_request_substitution(self, obj):
        return obj.can_request_substitution()
    
    # def get_extensions_count(self, obj):
    #     return obj.extensions.count()
    
    # def get_substitutions_count(self, obj):
    #     return obj.substitutions.count()


class ServiceOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceOrder
        fields = [
            'title',
            'service_request_id',
            'winning_offer_id',
            'contract_id',
            'start_date',
            # 'original_end_date',
            'current_end_date',
            'current_specialist_id',
            'current_specialist_name',
            # 'original_specialist_id',
            # 'original_specialist_name',
            'role',
            'domain',
            # 'original_man_days',
            'current_man_days',
            'daily_rate',
            'original_contract_value',
            'current_contract_value',
            'notes',
        ]
    
    def validate(self, data):
        # if data.get('current_end_date') != data.get('original_end_date'):
        #     raise serializers.ValidationError(
        #         "Current end date must match original end date on creation"
        #     )
        
        # if data.get('current_man_days') != data.get('original_man_days'):
        #     raise serializers.ValidationError(
        #         "Current man days must match original man days on creation"
        #     )
        
        # if data.get('current_specialist_id') != data.get('original_specialist_id'):
        #     raise serializers.ValidationError(
        #         "Current specialist must match original specialist on creation"
        #     )
        
        # Validate dates
        if data.get('start_date') and data.get('original_end_date'):
            if data['start_date'] >= data['original_end_date']:
                raise serializers.ValidationError(
                    "Start date must be before end date"
                )
        
        return data


class ServiceOrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceOrder
        fields = [
            'status',
            'consumed_man_days',
            'notes',
        ]
    
    def validate_consumed_man_days(self, value):
        if value > self.instance.current_man_days:
            raise serializers.ValidationError(
                f"Consumed man days cannot exceed current man days ({self.instance.current_man_days})"
            )
        return value