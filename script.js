class NationsRankings {
    constructor() {
        this.nations = [];
        this.init();
    }

    async init() {
        await this.loadData();
        this.setupEventListeners();
        this.showRichest();
    }

    async loadData() {
        try {
            const response = await fetch('nations_comprehensive.json');
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            const data = await response.json();
            
            // Apply nation merges
            this.nations = this.mergeNations(data);

            console.log(`Loaded ${this.nations.length} nations`);
            console.log('First nation:', this.nations[0]);
        } catch (error) {
            console.error('Error loading nation data:', error);
            this.nations = [];
        }
    }

    setupEventListeners() {
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
    }

    switchTab(tabName) {
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        switch(tabName) {
            case 'richest':
                this.showRichest();
                break;
            case 'largest':
                this.showLargest();
                break;
            case 'populous':
                this.showPopulous();
                break;
        }
    }
    
    // Updated to use unique_players for population
    showPopulous() {
        const sorted = [...this.nations]
            .filter(nation => nation.unique_players > 0)
            .sort((a, b) => b.unique_players - a.unique_players);

        this.renderRankings('populous-list', sorted, (nation) => ({
            primary: nation.unique_players.toLocaleString(),
            stats: [
                { label: `${nation.territories.length} cities` },
                { label: `${nation.total_chunks.toLocaleString()} chunks` },
                { label: this.formatCurrency(nation.total_balance) }
            ]
        }));
    }

    showRichest() {
        const sorted = [...this.nations]
            .filter(nation => nation.total_balance > 0)
            .sort((a, b) => b.total_balance - a.total_balance);

        this.renderRankings('richest-list', sorted, (nation) => ({
            primary: this.formatCurrency(nation.total_balance),
            stats: [
                { label: `${nation.territories.length} cities` },
                { label: `${nation.total_chunks.toLocaleString()} chunks` },
                { label: `${nation.unique_players} players` }
            ]
        }));
    }

    showLargest() {
        const sorted = [...this.nations]
            .filter(nation => nation.total_chunks > 0)
            .sort((a, b) => b.total_chunks - a.total_chunks);

        this.renderRankings('largest-list', sorted, (nation) => ({
            primary: `${nation.total_chunks.toLocaleString()}`,
            stats: [
                { label: `${nation.territories.length} cities` },
                { label: this.formatCurrency(nation.total_balance) },
                { label: `${nation.unique_players} players` }
            ]
        }));
    }

    // New method to merge nations based on the provided groups
    mergeNations(data) {
        const mergeGroups = {
            "Imperial Crownlands of Osentar": [
                "MayraSovereignty", "Vinovia", "Lenoria", "Osentar",
                "osentar_newteritory", "Kutaiyara", "Orion", "Nova_Stellare",
            ],
            "Eternal Empire of Bardonia": [
                "Bardonia", "Seneca-Diarchy", "Varaxis-Imperium", "Regnum_Aquilarum"
            ]
        };

        const mergedNations = new Map();
        const nationsToMerge = new Set(Object.values(mergeGroups).flat());

        for (const nation of data) {
            let isMerged = false;
            for (const [groupName, members] of Object.entries(mergeGroups)) {
                if (members.includes(nation.name)) {
                    if (!mergedNations.has(groupName)) {
                        mergedNations.set(groupName, {
                            name: groupName,
                            level: 'Empire', // Set a default level for the merged group
                            territories: new Set(),
                            total_chunks: 0,
                            total_balance: 0,
                            unique_players: new Set(),
                        });
                    }
                    
                    const mergedGroup = mergedNations.get(groupName);
                    mergedGroup.total_chunks += nation.total_chunks;
                    mergedGroup.total_balance += nation.total_balance;
                    nation.territories.forEach(t => mergedGroup.territories.add(t));
                    nation.all_players.forEach(p => mergedGroup.unique_players.add(p));

                    isMerged = true;
                    break;
                }
            }
            if (!isMerged && !nationsToMerge.has(nation.name)) {
                mergedNations.set(nation.name, {
                    ...nation,
                    territories: new Set(nation.territories),
                    unique_players: new Set(nation.all_players),
                });
            }
        }

        // Convert sets back to arrays and format data
        const finalNations = [];
        for (const nation of mergedNations.values()) {
            finalNations.push({
                ...nation,
                territories: Array.from(nation.territories),
                unique_players: nation.unique_players.size,
                all_players: Array.from(nation.unique_players)
            });
        }
        
        return finalNations;
    }

    renderRankings(containerId, nations, getDisplayData) {
        const container = document.getElementById(containerId);

        container.innerHTML = `
            <table class="rankings">
                ${nations.map((nation, index) => {
                    const displayData = getDisplayData(nation);
                    const rank = index + 1;

                    return `
                        <tr class="nation-card">
                            <td class="rank">${rank}</td>
                            <td class="nation-info">
                                <div class="nation-name">${this.escapeHtml(nation.name)}</div>
                                <div class="nation-level">${this.escapeHtml(nation.level || '—')}</div>
                                <div class="nation-stats">
                                    ${displayData.stats.map(stat => 
                                        `<span class="stat">${stat.label}</span>`
                                    ).join(' • ')}
                                </div>
                            </td>
                            <td class="primary-value">${displayData.primary}</td>
                        </tr>
                    `;
                }).join('')}
            </table>
        `;
    }

    formatCurrency(amount) {
        if (amount >= 1_000_000_000) {
            return `$${(amount / 1_000_000_000).toFixed(1)}B`;
        } else if (amount >= 1_000_000) {
            return `$${(amount / 1_000_000).toFixed(1)}M`;
        } else if (amount >= 1_000) {
            return `$${(amount / 1_000).toFixed(1)}K`;
        } else {
            return `$${amount.toFixed(0)}`;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new NationsRankings();
});